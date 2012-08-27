
------------------
-- t_change_log --
------------------

CREATE TABLE services.t_change_log
( t_change_log_id serial NOT NULL PRIMARY KEY,
  created timestamptz DEFAULT NOW(),
  table_ref oid NOT NULL,
  event_type t_change_log_event_type NOT NULL,
  data_id integer NOT NULL,
  transaction_id bigint NOT NULL DEFAULT txid_current(),
  username text NOT NULL DEFAULT "session_user"()
);

COMMENT ON COLUMN services.t_change_log.event_type IS 'INSERT, UPDATE, DELETE';
GRANT USAGE ON services.t_change_log_t_change_log_id_seq to users;

GRANT SELECT ON services.t_change_log TO admins;

CREATE OR REPLACE RULE t_change_log_insert_notify
AS
ON INSERT TO services.t_change_log
DO ALSO
NOTIFY sqlobjectupdate;

CREATE OR REPLACE VIEW services.change_log
AS
SELECT t_change_log.t_change_log_id, t_change_log.created, t_change_log.table_ref, t_change_log.event_type, t_change_log.data_id,
t_change_log.transaction_id, pg_class.relname as table, t_change_log.username as username
FROM services.t_change_log
JOIN pg_catalog.pg_class ON (t_change_log.table_ref = pg_class.oid);

GRANT SELECT ON services.change_log TO servers;
GRANT SELECT ON services.change_log TO admins;

-- CUSTOMERS
-- You maybe want to use a somekind of wrapper for this, but this is the default way to do this.

CREATE TABLE services.t_customers (
    t_customers_id integer NOT NULL PRIMARY KEY,
    name text NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    closed timestamp with time zone
);

GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_customers TO admins;

SELECT services.create_log_triggers('services.t_customers'::text);

-- mainly for Kapsi's needs

CREATE TABLE services.t_aliases
(
    t_aliases_id serial NOT NULL PRIMARY KEY,
    t_customers_id integer references services.t_customers NOT NULL,
    alias text NOT NULL UNIQUE
);

SELECT services.create_log_triggers('services.t_aliases'::text);

GRANT SELECT,UPDATE,INSERT,DELETE ON services.t_aliases TO admins;
GRANT USAGE ON services.t_aliases_t_aliases_id_seq TO admins;


-- DOMAINS

CREATE TABLE services.t_domains (
    t_domains_id serial NOT NULL PRIMARY KEY,
    name text UNIQUE NOT NULL,
    shared boolean DEFAULT false NOT NULL,
    t_customers_id integer REFERENCES services.t_customers NOT NULL,
    dns boolean DEFAULT true NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    updated timestamp with time zone DEFAULT now(),
    refresh_time integer DEFAULT 28800 NOT NULL,
    retry_time integer DEFAULT 7200 NOT NULL,
    expire_time integer DEFAULT 1209600 NOT NULL,
    minimum_cache_time integer DEFAULT 21600 NOT NULL,
    ttl integer DEFAULT 10800 NOT NULL,
    admin_address text DEFAULT 'hostmaster@example.com'::text NOT NULL,
    domain_type domain_type DEFAULT 'MASTER'::domain_type NOT NULL,
    masters inet[],
    allow_transfer inet[]
);

SELECT services.create_log_triggers('services.t_domains'::text);

ALTER TABLE servicest_domains ADD CONSTRAINT "domains_check" CHECK (
    refresh_time >= 1
    AND refresh_time <= 9999999
    AND retry_time >= 1
    AND retry_time <= 9999999
    AND expire_time >= 1
    AND expire_time <= 9999999
    AND minimum_cache_time >= 1
    AND minimum_cache_time <= 9999999
    AND ttl >= 1
    AND ttl <= 9999999);

ALTER TABLE services.t_domains ADD CONSTRAINT "valid_admin_address" CHECK (
    admin_address ~ '^[^@\s]+@[^@\s]+(\.[^@\s]+)+$');


GRANT INSERT,UPDATE,SELECT,DELETE ON services.t_domains TO admins;
GRANT SELECT ON services.t_domains TO servers;


CREATE TABLE services.t_dns_keys (
    t_dns_keys_id integer PRIMARY KEY NOT NULL,
    name text NOT NULL,
    algorithm text NOT NULL,
    key text NOT NULL,
    description text
);

-- Many to many relation

CREATE TABLE services.t_domain_dns_keys (
    t_domains_id integer NOT NULL,
    t_dns_keys_id integer NOT NULL
);

SELECT services.create_log_triggers('services.t_dns_keys'::text);

-- USERS

CREATE TABLE services.t_users (
    t_users_id serial NOT NULL PRIMARY KEY,
    t_customers_id integer NOT NULL REFERENCES services.t_customers,
    created timestamp with time zone DEFAULT now() NOT NULL,
    name text NOT NULL UNIQUE,
    lastname text,
    firstnames text,
    phone text,
    unix_id integer UNIQUE,
    password_changed timestamp with time zone DEFAULT now() NOT NULL,
    t_domains_id integer references services.t_domains NOT NULL
);

GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_users TO admins;
GRANT SELECT ON services.t_users TO servers;

SELECT services.create_log_triggers('services.t_users'::text);

CREATE OR REPLACE VIEW public.users AS
    SELECT t_users.t_customers_id, t_users.name, t_users.lastname, t_users.firstnames, t_users.phone,
    t_users.unix_id, t_users.t_users_id, t_users.t_domains_id, public.is_admin(t_users.name) as admin
    FROM services.t_users
    WHERE (t_users.name = ("current_user"())::text OR public.is_admin());

GRANT SELECT ON public.users TO users;
GRANT SELECT ON public.users TO admins;

CREATE OR REPLACE VIEW public.customers AS
SELECT t_customers.t_customers_id, t_customers.name, array_agg(distinct t_aliases.alias) as aliases
FROM services.t_customers
JOIN services.t_users USING (t_customers_id)
LEFT JOIN services.t_aliases USING (t_customers_id)
WHERE (t_users.name = CURRENT_USER OR public.is_admin())
GROUP BY t_customers.t_customers_id;

GRANT SELECT ON public.customers TO users;
GRANT SELECT ON public.customers TO admins;

-- Domains view

CREATE OR REPLACE VIEW public.domains
AS
SELECT t_domains.t_domains_id, t_domains.name, t_domains.shared, t_domains.t_customers_id,
t_domains.dns, t_domains.created, t_domains.updated, t_domains.refresh_time, t_domains.retry_time,
t_domains.expire_time, t_domains.minimum_cache_time, t_domains.ttl, t_domains.admin_address,
t_domains.domain_type, t_domains.masters, t_domains.allow_transfer
FROM services.t_domains
JOIN services.t_customers USING (t_customers_id)
JOIN services.t_users USING (t_customers_id)
WHERE ((( t_users.name = "current_user"()::text AND public.is_admin() IS FALSE) OR t_domains.shared = TRUE ) OR public.is_admin())
-- if there many users in one customers
GROUP BY t_domains.t_domains_id;

CREATE OR REPLACE RULE domains_insert
AS ON INSERT TO public.domains
DO INSTEAD
INSERT INTO services.t_domains
(t_customers_id, name, shared,dns,refresh_time,retry_time,expire_time,minimum_cache_time,ttl,admin_address,domain_type,masters,allow_transfer)
SELECT DISTINCT(t_customers_id),
NEW.name,
NEW.shared,
NEW.dns,
NEW.refresh_time,
NEW.retry_time,
NEW.expire_time,
NEW.minimum_cache_time,
NEW.ttl,
NEW.admin_address,
NEW.domain_type,
NEW.masters,
NEW.allow_transfer
FROM users
WHERE ( users.name = CURRENT_USER AND NOT public.is_admin()) OR ( public.is_admin() = true AND users.t_customers_id = NEW.t_customers_id )
AND (select COUNT(domains.t_domains_id) FROM domains, users WHERE users.name = CURRENT_USER AND domains.t_customers_id = users.t_customers_id) < 50
RETURNING t_domains.t_domains_id,
t_domains.name, t_domains.shared,
t_domains.t_customers_id, t_domains.dns,
t_domains.created, t_domains.updated,
t_domains.refresh_time, t_domains.retry_time,
t_domains.expire_time, t_domains.minimum_cache_time,
t_domains.ttl, t_domains.admin_address,
t_domains.domain_type, t_domains.masters,
t_domains.allow_transfer
;

CREATE OR REPLACE RULE
domains_update AS
ON UPDATE TO domains
DO INSTEAD
UPDATE t_domains
SET name = new.name,
shared=new.shared,
dns=new.dns,
refresh_time=new.refresh_time,
retry_time=new.retry_time,
expire_time=new.expire_time,
minimum_cache_time=new.minimum_cache_time,
ttl=new.ttl,
admin_address=new.admin_address,
domain_type=new.domain_type,
masters=new.masters,
allow_transfer=new.allow_transfer
FROM services.t_customers, services.t_users
WHERE t_domains.t_domains_id = new.t_domains_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (( t_users.name = CURRENT_USER AND NOT public.is_admin()) OR public.is_admin());

CREATE OR REPLACE RULE domains_delete
AS ON DELETE TO domains
DO INSTEAD
DELETE FROM services.t_domains USING services.t_customers, services.t_users
WHERE t_domains.t_domains_id = OLD.t_domains_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (( t_users.name = CURRENT_USER AND NOT public.is_admin()) OR public.is_admin());
--LIMIT 50;

ALTER TABLE public.domains ALTER shared SET DEFAULT false;
ALTER TABLE public.domains ALTER dns SET DEFAULT true;
ALTER TABLE public.domains ALTER refresh_time SET DEFAULT 28800;
ALTER TABLE public.domains ALTER retry_time SET DEFAULT 7200;
ALTER TABLE public.domains ALTER minimum_cache_time SET DEFAULT 21600;
ALTER TABLE public.domains ALTER expire_time SET DEFAULT 1209600;
ALTER TABLE public.domains ALTER ttl SET DEFAULT 10800;
ALTER TABLE public.domains ALTER domain_type SET DEFAULT 'MASTER';
ALTER TABLE public.domains ALTER admin_address SET DEFAULT 'hostmaster@example.com';

GRANT SELECT,INSERT,UPDATE,DELETE ON public.domains TO users;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.domains TO admins;
GRANT USAGE ON services.t_domains_t_domains_id_seq TO users;
GRANT USAGE ON services.t_domains_t_domains_id_seq TO admins;


-- DNS-entries table

CREATE TABLE services.t_dns_entries
(
    t_dns_entries_id serial PRIMARY KEY NOT NULL,
    ttl INTEGER NOT NULL DEFAULT 3600,
    type t_dns_entries_type NOT NULL,
    key text NOT NULL,
    value text NOT NULL,
    manual boolean NOT NULL default FALSE,
    t_domains_id integer references services.t_domains NOT NULL,
    info text
);

SELECT services.create_log_triggers('services.t_dns_entries'::text);

GRANT SELECT ON services.t_dns_entries TO servers;
GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_dns_entries TO admins;
