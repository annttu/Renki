
--------------
-- Services --
--------------
-- Contains services on this environment

CREATE TABLE services.t_service_types
(
    t_service_type_id serial PRIMARY KEY NOT NULL,
    service_type text NOT NULL UNIQUE,
    service_category text NOT NULL
);

CREATE TABLE services.t_services
(
    t_services_id serial NOT NULL PRIMARY KEY,
    t_addresses_id integer references t_addresses,
    service_type text references t_service_types (service_type) NOT NULL,
    t_domains_id integer references t_domains NOT NULL,
    info text,
    active boolean DEFAULT true NOT NULL,
    -- can users view this?
    public boolean DEFAULT false NOT NULL,
    UNIQUE (t_addresses_id, service_type)
);

GRANT USAGE ON services.t_services_t_services_id_seq TO admins;
GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_services TO admins;
GRANT SELECT ON services.t_services TO servers;

SELECT create_log_triggers('services.t_services'::text);

-- Populate t_service_types
insert into t_service_types (service_category, service_type) VALUES ('DATABASE','MYSQL');
insert into t_service_types (service_category, service_type) VALUES ('DATABASE','POSTGRESQL');
insert into t_service_types (service_category, service_type) VALUES ('MAIL','MAIL');
insert into t_service_types (service_category, service_type) VALUES ('MAIL','MAILLIST');
insert into t_service_types (service_category, service_type) VALUES ('VHOST','VHOST');
insert into t_service_types (service_category, service_type) VALUES ('VHOST','WORDPRESS');
insert into t_service_types (service_category, service_type) VALUES ('SHELL','USER_PORT');
insert into t_service_types (service_category, service_type) VALUES ('SHELL','SHELL');
insert into t_service_types (service_category, service_type) VALUES ('OTHER','JABBER');


----------------
-- User ports --
----------------

-- ports are hosts functionality
-- ports are for users on shell servers

CREATE TABLE services.t_user_ports
(
    t_user_ports_id serial PRIMARY KEY NOT NULL,
    t_users_id integer references t_users NOT NULL,
    port integer NOT NULL,
    info text,
    t_services_id integer references t_services NOT NULL,
    approved boolean NOT NULL DEFAULT false,
    active boolean NOT NULL DEFAULT true
);

ALTER TABLE t_user_ports ADD CONSTRAINT valid_port CHECK ((port > 1024 AND port <= 30000 ) OR ( port >= 40000 AND port < 65536));
ALTER TABLE t_user_ports ADD UNIQUE (port, t_services_id);

SELECT services.create_log_triggers('services.t_user_ports'::text);

CREATE OR REPLACE VIEW public.user_port_servers
AS
SELECT
t_services.t_services_id as t_services_id,
public.find_free_port(t_services.t_services_id) as port,
t_addresses.name || '.' || t_domains.name as server
FROM t_services
JOIN t_addresses ON t_services.t_addresses_id = t_addresses.t_addresses_id
JOIN t_domains ON (t_services.t_domains_id = t_domains.t_domains_id)
JOIN users ON users.name = CURRENT_USER
JOIN t_customers ON (t_customers.t_customers_id = users.t_customers_id)
WHERE t_services.service_type = 'USER_PORT'
AND t_services.public = TRUE
AND t_services.active = TRUE
AND ( t_services.t_domains_id = users.t_domains_id OR public.is_admin());

GRANT SELECT ON public.user_port_servers TO users;
GRANT SELECT ON public.user_port_servers TO admins;

CREATE OR REPLACE VIEW public.user_ports
AS
SELECT
t_user_ports.t_user_ports_id,
t_user_ports.t_users_id,
t_users.t_customers_id,
t_users.name as username,
port,
t_addresses.name || '.' || t_domains.name as server,
t_user_ports.info as info,
t_user_ports.approved,
t_user_ports.active
FROM t_user_ports
JOIN t_users USING (t_users_id)
JOIN t_services USING (t_services_id)
JOIN t_addresses ON t_addresses.t_addresses_id = t_services.t_addresses_id
JOIN t_domains ON t_addresses.t_domains_id = t_domains.t_domains_id
WHERE ( t_users.name = CURRENT_USER OR public.is_admin())
AND t_user_ports.t_users_id = t_users.t_users_id;

ALTER TABLE public.user_ports ALTER active SET DEFAULT true;

GRANT SELECT ON public.user_ports TO users;
GRANT SELECT ON public.user_ports TO admins;
GRANT USAGE ON t_user_ports_t_user_ports_id_seq TO users;
GRANT USAGE ON t_user_ports_t_user_ports_id_seq TO admins;

CREATE OR REPLACE RULE user_ports_insert
AS ON INSERT
TO public.user_ports
DO INSTEAD
INSERT INTO t_user_ports
(t_users_id, port, t_services_id, info, approved, active)
SELECT users.t_users_id, user_port_servers.port, user_port_servers.t_services_id, NEW.info,
    (SELECT COUNT(user_ports.t_user_ports_id)
     FROM user_ports, users
     WHERE users.name = CURRENT_USER
     AND user_ports.t_users_id = users.t_users_id) < 5,
new.active
FROM users, user_port_servers
WHERE (
        (users.name = CURRENT_USER  AND NOT public.is_admin())
    OR
    (public.is_admin()
    AND (
        (NEW.t_users_id is NOT NULL AND users.t_users_id = NEW.t_users_id)
        OR
        (NEW.username IS NOT NULL AND users.name = NEW.username)
        )
    )
)
AND (SELECT COUNT(user_ports.t_user_ports_id) FROM user_ports, users  WHERE users.name = CURRENT_USER AND user_ports.t_users_id = users.t_users_id) < 20
AND user_port_servers.server = NEW.server
RETURNING t_user_ports_id,t_users_id, (SELECT users.t_customers_id as t_customers_id FROM users WHERE users.t_users_id = t_user_ports.t_users_id),
(SELECT users.name from users WHERE users.t_users_id = t_user_ports.t_users_id), port,
(SELECT user_port_servers.server FROM user_port_servers WHERE user_port_servers.t_services_id = t_user_ports.t_services_id ),
t_user_ports.info, t_user_ports.approved, t_user_ports.active;

GRANT INSERT ON user_ports TO users;
GRANT INSERT ON user_ports TO admins;

CREATE OR REPLACE RULE user_ports_update
AS ON UPDATE
TO public.user_ports
DO INSTEAD
(
UPDATE t_user_ports SET
active = NEW.active,
info = NEW.info,
approved = ((public.is_admin() AND NEW.approved ) OR (OLD.approved))
FROM t_customers, users
WHERE t_user_ports.t_user_ports_id = new.t_user_ports_id
AND t_user_ports.t_users_id = users.t_users_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_users_id = OLD.t_users_id))
RETURNING t_user_ports.t_user_ports_id, t_user_ports.t_users_id, (SELECT users.t_customers_id as t_customers_id FROM users WHERE users.t_users_id = t_user_ports.t_users_id),
(SELECT users.name from users WHERE users.t_users_id = t_user_ports.t_users_id), port,
(SELECT user_port_servers.server FROM user_port_servers WHERE user_port_servers.t_services_id = t_user_ports.t_services_id ),
t_user_ports.info, t_user_ports.approved, t_user_ports.active;
);

GRANT UPDATE ON user_ports TO users;
GRANT UPDATE ON user_ports TO admins;

CREATE OR REPLACE RULE user_ports_delete
AS ON DELETE
TO public.user_ports
DO INSTEAD
(
DELETE FROM t_user_ports USING t_customers, t_users
WHERE t_user_ports.t_user_ports_id = OLD.t_user_ports_id
AND t_user_ports.t_users_id = t_users.t_users_id
AND t_users.t_customers_id = t_customers.t_customers_id
AND (t_users.name = CURRENT_USER OR public.is_admin())
RETURNING t_user_ports.t_user_ports_id, t_user_ports.t_users_id, (SELECT users.t_customers_id as t_customers_id FROM users WHERE users.t_users_id = t_user_ports.t_users_id),
(SELECT users.name from users WHERE users.t_users_id = t_user_ports.t_users_id), port,
(SELECT user_port_servers.server FROM user_port_servers WHERE user_port_servers.t_services_id = t_user_ports.t_services_id ),
t_user_ports.info, t_user_ports.approved, t_user_ports.active
);

GRANT DELETE ON user_ports TO users;
GRANT DELETE ON user_ports TO admins;

---------------
-- Databases --
---------------

CREATE TABLE services.t_databases
(
    t_databases_id serial PRIMARY KEY NOT NULL,
    database_name text NOT NULL,
    username text NOT NULL,
    t_services_id integer references t_services NOT NULL,
    t_customers_id integer references t_customers NOT NULL,
    info text,
    approved boolean DEFAULT FALSE NOT NULL,
    UNIQUE (database_name, t_services_id)
);

ALTER TABLE services.t_databases ADD CONSTRAINT valid_database_name CHECK (database_name ~* '^[a-z0-9_]+$');
ALTER TABLE services.t_databases ADD CONSTRAINT valid_username CHECK (database_name ~* '^[a-z0-9_]+$');

GRANT USAGE ON services.t_databases_t_databases_id_seq TO users;
GRANT USAGE ON services.t_databases_t_databases_id_seq TO admins;
GRANT SELECT,UPDATE,DELETE,INSERT ON services.t_databases TO admins;
GRANT SELECT ON services.t_databases TO users;

-- create log rules
SELECT services.create_log_triggers('services.t_databases'::text);

-- Database servers view

DROP VIEW IF EXISTS public.database_servers;
CREATE OR REPLACE VIEW public.database_servers
AS
SELECT t_services_id, t_addresses.name || '.' || t_domains.name as server,
t_services.service_type AS database_type, t_services.active
FROM t_services
JOIN t_addresses USING (t_addresses_id)
JOIN t_hosts USING (t_hosts_id)
JOIN t_domains ON t_services.t_domains_id = t_domains.t_domains_id
JOIN t_users ON CURRENT_USER = t_users.name
JOIN t_service_types USING (service_type)
WHERE t_service_types.service_category = 'DATABASE'
AND t_services.public = True
AND (t_users.t_domains_id = t_services.t_domains_id OR public.is_admin() = True);

GRANT SELECT ON public.database_servers TO users;
GRANT SELECT ON public.database_servers TO admins;

-- databases view

DROP VIEW IF EXISTS public.databases;
CREATE OR REPLACE VIEW public.databases
AS
SELECT DISTINCT t_databases.t_databases_id, t_databases.database_name, t_databases.username, t_databases.t_customers_id,
t_databases.approved, t_services.service_type AS database_type,
t_addresses.name || '.' || t_domains.name AS server, t_databases.info
FROM t_databases
JOIN t_customers ON t_databases.t_customers_id = t_customers.t_customers_id
JOIN t_users ON t_users.t_customers_id = t_customers.t_customers_id
JOIN t_services USING (t_services_id)
JOIN t_addresses USING (t_addresses_id)
JOIN t_domains ON t_addresses.t_domains_id = t_domains.t_domains_id
WHERE (t_users.name = CURRENT_USER OR public.is_admin() = true)
;

GRANT SELECT ON public.databases TO users;
GRANT SELECT ON public.databases TO admins;

CREATE OR REPLACE RULE databases_insert
AS
ON INSERT TO public.databases
DO INSTEAD
(
INSERT INTO services.t_databases
    (database_name, username, t_customers_id, info, t_services_id, approved)
    SELECT DISTINCT NEW.database_name, NEW.username, t_customers.t_customers_id, NEW.info,
    database_servers.t_services_id,
    (
        public.is_admin()
        OR (
            public.valid_database_name(NEW.database_name)
            AND (SELECT COUNT(t_databases_id) FROM databases
            JOIN users ON (databases.t_customers_id = users.t_customers_id AND users.name = session_user)
            WHERE databases.t_customers_id = users.t_customers_id
            ) < 10
        )
    )
    FROM t_customers
    JOIN database_servers ON (database_servers.active = True)
    JOIN users ON (t_customers.t_customers_id = users.t_customers_id)
    WHERE (
        (users.name = CURRENT_USER  AND NOT public.is_admin() AND users.t_customers_id = t_customers.t_customers_id)
    OR
    ( public.is_admin() AND t_customers.t_customers_id = NEW.t_customers_id )
    )
    AND NEW.server = database_servers.server
    AND NEW.database_type = database_servers.database_type
    AND (
            SELECT COUNT(t_databases_id) FROM databases
            WHERE databases.t_customers_id = t_customers.t_customers_id
    ) < 20
    RETURNING t_databases.t_databases_id, t_databases.database_name, t_databases.username, t_databases.t_customers_id,
    t_databases.approved, (SELECT t_services.service_type FROM t_services WHERE t_services.t_services_id = t_databases.t_services_id),
    (SELECT t_addresses.name || '.' || t_domains.name
        FROM t_services
        JOIN t_addresses USING (t_addresses_id)
        JOIN t_domains ON (t_domains.t_domains_id = t_addresses.t_domains_id)
        WHERE t_services.t_services_id = t_databases.t_services_id),
    t_databases.info;
);

GRANT INSERT ON databases TO users;
GRANT INSERT ON databases TO admins;

CREATE OR REPLACE RULE databases_update
AS ON UPDATE
TO public.databases
DO INSTEAD
(
UPDATE services.t_databases SET
info = NEW.info,
approved = ((public.is_admin() AND NEW.approved) OR OLD.approved)
FROM t_customers, users
WHERE t_databases.t_databases_id = new.t_databases_id
AND t_databases.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id));
);

GRANT UPDATE ON databases TO users;
GRANT UPDATE ON databases TO admins;

CREATE OR REPLACE RULE databases_delete
AS
ON DELETE TO public.databases
DO INSTEAD
(
    DELETE FROM t_databases
    USING t_customers, t_users
    WHERE t_databases.t_databases_id = OLD.t_databases_id
    AND t_databases.t_customers_id = t_users.t_customers_id
    AND t_users.t_customers_id = t_customers.t_customers_id
    AND (t_users.name = CURRENT_USER OR public.is_admin());
);

GRANT DELETE ON databases TO users;
GRANT DELETE ON databases TO admins;
