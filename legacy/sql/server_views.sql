
------------------
-- Server views --
------------------

CREATE OR REPLACE VIEW services.s_vhosts
AS
SELECT t_vhosts.t_vhosts_id, t_customers.t_customers_id, t_users.name as username, t_vhosts.t_users_id, t_vhosts.created,
vhostdomaincat(t_vhosts.name, t_dom.name::text) as name,
array_agg(distinct vhostdomaincat(t_vhost_aliases.name::text,t_aliases_domains.name::text)::text) as aliases,
array_agg(distinct vhostdomaincat(t_vhost_redirects.name::text,t_redirects_domains.name::text)::text) as redirects,
t_vhosts.redirect_to,
t_vhosts.logaccess,
t_vhosts.locked,
t_users.unix_id
FROM services.t_vhosts
JOIN services.t_domains as t_dom ON (t_vhosts.t_domains_id = t_dom.t_domains_id)
JOIN services.t_users ON (t_users.t_users_id = t_vhosts.t_users_id)
JOIN services.t_customers ON (t_users.t_customers_id = t_customers.t_customers_id)
LEFT JOIN services.t_vhosts AS t_vhost_aliases ON (t_vhosts.t_vhosts_id = t_vhost_aliases.parent_id
    AND NOT t_vhost_aliases.is_redirect
    AND t_vhost_aliases.redirect_to IS NULL
    AND t_vhost_aliases.t_users_id = t_users.t_users_id)
LEFT JOIN services.t_vhosts AS t_vhost_redirects ON (t_vhosts.t_vhosts_id = t_vhost_redirects.parent_id
    AND t_vhost_redirects.is_redirect
    AND t_vhost_redirects.redirect_to IS NULL
    AND t_vhost_redirects.t_users_id = t_users.t_users_id)
LEFT JOIN services.t_domains AS t_aliases_domains ON (t_aliases_domains.t_domains_id = t_vhost_aliases.t_domains_id)
LEFT JOIN services.t_domains AS t_redirects_domains ON (t_redirects_domains.t_domains_id = t_vhost_redirects.t_domains_id)
WHERE t_vhosts.parent_id IS NULL
AND t_users.t_customers_id = t_customers.t_customers_id
GROUP BY t_vhosts.t_vhosts_id,t_dom.name,t_customers.t_customers_id,t_users.name,t_users.unix_id;


GRANT SELECT ON s_vhosts TO servers;
GRANT SELECT ON s_vhosts TO admins;
SELECT create_history_table('s_vhosts');
ALTER TABLE s_vhosts_history SET SCHEMA services;
GRANT SELECT ON s_vhosts_history TO servers;
GRANT SELECT ON s_vhosts_history TO admins;

-- t_vhosts changes logged

CREATE OR REPLACE FUNCTION t_vhosts_backup_s_vhosts_trigger()
RETURNS TRIGGER
AS $t$
BEGIN
IF (TG_OP = 'DELETE') THEN
    EXECUTE 'SELECT historize_view($$s_vhosts$$::text, $$t_vhosts_id$$::text, ' || OLD.t_vhosts_id::text || '::text)';
    IF (OLD.parent_id IS NOT NULL) THEN
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || OLD.parent_id || ', $$UPDATE$$)';
    ELSE
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || OLD.t_vhosts_id || ', $$DELETE$$)';
    END IF;
    RETURN OLD;
ELSIF (TG_OP = 'UPDATE') THEN
    IF (NEW.t_domains_id != OLD.t_domains_id
        or NEW.t_users_id != OLD.t_users_id
        or NEW.www_servers_id != OLD.www_servers_id
        or NEW.name != OLD.name
        or NEW.is_redirect != OLD.is_redirect
        or NEW.logaccess != OLD.logaccess
        or NEW.redirect_to != OLD.redirect_to
        or NEW.locked != OLD.locked)
    THEN
        EXECUTE 'SELECT historize_view($$s_vhosts$$::text, $$t_vhosts_id$$::text, ' || NEW.t_vhosts_id::text || '::text )';
        IF (NEW.parent_id IS NOT NULL) THEN
            EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || OLD.parent_id || ', $$UPDATE$$)';
        ELSE
            EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || OLD.t_vhosts_id || ', $$UPDATE$$)';
        END IF;
    END IF;
    RETURN NEW;
ELSIF (TG_OP = 'INSERT') THEN
    IF (NEW.parent_id IS NOT NULL) THEN
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || NEW.parent_id || ', $$UPDATE$$)';
    ELSE
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || NEW.t_vhosts_id || ', $$INSERT$$)';
    END IF;
    RETURN NEW;
END IF;

END;
$t$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_vhosts_updatedelete_backup_s_vhosts ON t_vhosts;
CREATE TRIGGER t_vhosts_update_delete_backup_s_vhosts
BEFORE UPDATE OR DELETE
ON t_vhosts
FOR EACH ROW
EXECUTE PROCEDURE t_vhosts_backup_s_vhosts_trigger();

DROP TRIGGER IF EXISTS t_vhosts_insert_backup_s_vhosts ON t_vhosts;
CREATE TRIGGER t_vhosts_insert_backup_s_vhosts
AFTER INSERT
ON t_vhosts
FOR EACH ROW
EXECUTE PROCEDURE t_vhosts_backup_s_vhosts_trigger();

----------------------------------------
-- t_users changes to s_vhosts logged --
----------------------------------------

CREATE OR REPLACE FUNCTION t_users_backup_s_vhosts_trigger()
RETURNS TRIGGER
AS $t$
DECLARE
    row record;
BEGIN
IF (TG_OP = 'UPDATE') THEN
    IF (NEW.t_users_id != OLD.t_users_id
        or NEW.name != OLD.name
        or (NEW.unix_id::text IS DISTINCT FROM OLD.unix_id::text)
    )
    THEN
        EXECUTE 'SELECT historize_view($$s_vhosts$$::text, $$t_users_id$$::text, ' || OLD.t_users_id::text || '::text)';
        FOR row IN SELECT t_vhosts_id FROM s_vhosts WHERE t_users_id = OLD.t_users_id LOOP
            EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || row.t_vhosts_id || ', $$UPDATE$$)';
        END LOOP;
    END IF;
    RETURN NEW;
END IF;
END;
$t$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_users_update_backup_s_vhosts ON t_users;
CREATE TRIGGER t_users_update_backup_s_vhosts
BEFORE UPDATE
ON t_users
FOR EACH ROW
EXECUTE PROCEDURE t_users_backup_s_vhosts_trigger();

/*
-- useless
DROP TRIGGER IF EXISTS t_users_delete_backup_s_vhosts ON t_users;
CREATE TRIGGER t_users_delete_backup_s_vhosts
AFTER INSERT
ON t_users
FOR EACH ROW
EXECUTE PROCEDURE t_users_backup_s_vhosts_trigger();*/

--- domains ---

CREATE OR REPLACE FUNCTION t_domains_backup_s_vhosts_trigger()
RETURNS TRIGGER
AS $t$
DECLARE
    row record;
BEGIN
IF (TG_OP = 'UPDATE') THEN
    IF (NEW.t_domains_id != OLD.t_domains_id
        or NEW.name != OLD.name)
    THEN
        EXECUTE 'SELECT historize_view($$s_vhosts$$::text, $$t_domains_id$$::text, ' || NEW.t_domains_id::text || '::text )';
        FOR row IN SELECT t_vhosts_id, parent_id FROM s_vhosts WHERE t_domains_id = OLD.t_domains_id LOOP
            IF (row.parent_id IS NOT NULL) THEN
                EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || row.parent_id || ', $$UPDATE$$)';
            ELSE
                EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_vhosts$$::regclass::oid, ' || row.t_vhosts_id || ', $$UPDATE$$)';
            END IF;
        END LOOP;
    END IF;
    RETURN NEW;
END IF;

END;
$t$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_domains_update_backup_s_vhosts ON t_domains;
CREATE TRIGGER t_domains_update_backup_s_vhosts
BEFORE UPDATE
ON t_domains
FOR EACH ROW
EXECUTE PROCEDURE t_domains_backup_s_vhosts_trigger();

-----------------------
-- t_domains history --
-----------------------

SELECT create_history_table('t_domains');
ALTER TABLE t_domains_history SET SCHEMA services;
GRANT select ON t_domains_history TO servers;
GRANT select ON t_domains_history TO admins;


DROP FUNCTION IF EXISTS t_domains_historize_trigger();
CREATE OR REPLACE FUNCTION t_domains_historize_trigger()
RETURNS TRIGGER
AS $trigger$
BEGIN
IF (TG_OP = 'UPDATE') THEN
    EXECUTE 'SELECT historize_view($$t_domains$$::text, $$t_domains_id$$::text, ' || NEW.t_domains_id::text || '::text )';
    RETURN NEW;
ELSIF (TG_OP = 'DELETE') THEN
    EXECUTE 'SELECT historize_view($$t_domains$$::text, $$t_domains_id$$::text, ' || OLD.t_domains_id::text || '::text )';
    RETURN OLD;
END IF;
RETURN NEW;
END;
$trigger$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_domains_update ON t_domains;
CREATE TRIGGER t_domains_update
BEFORE UPDATE
ON t_domains
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE PROCEDURE t_domains_historize_trigger();

DROP TRIGGER IF EXISTS t_domains_delete ON t_domains;
CREATE TRIGGER t_domains_delete
BEFORE DELETE
ON t_domains
FOR EACH ROW
EXECUTE PROCEDURE t_domains_historize_trigger();

-----------
-- PORTS --
-----------

DROP VIEW IF EXISTS services.s_user_ports;
CREATE OR REPLACE VIEW services.s_user_ports
AS
SELECT t_user_ports.t_user_ports_id, t_user_ports.t_users_id, t_user_ports.port, t_user_ports.info, t_user_ports.t_services_id,
t_user_ports.approved, t_user_ports.active, t_users.name, t_users.t_customers_id, t_users.unix_id,
(t_addresses.name || '.'::text) || t_domains.name AS server, t_addresses.t_hosts_id as t_hosts_id, t_users.name as username
FROM services.t_user_ports
JOIN services.t_users USING (t_users_id)
JOIN services.t_customers ON t_users.t_customers_id = t_customers.t_customers_id
JOIN services.t_services USING (t_services_id)
JOIN services.t_addresses ON (t_services.t_addresses_id = t_addresses.t_addresses_id)
JOIN services.t_domains ON t_addresses.t_domains_id = t_domains.t_domains_id
WHERE t_user_ports.t_services_id = t_services.t_services_id;

GRANT SELECT ON services.s_user_ports TO servers;
GRANT SELECT ON services.s_user_ports TO admins;

SELECT create_history_table('s_user_ports'::text);
ALTER TABLE s_user_ports_history SET SCHEMA services;
GRANT SELECT ON services.s_user_ports_history TO servers;
GRANT SELECT ON services.s_user_ports_history TO admins;

DROP FUNCTION IF EXISTS t_users_historize_s_user_ports_trigger();
CREATE OR REPLACE FUNCTION t_users_historize_s_user_ports_trigger()
RETURNS TRIGGER
AS $t$
DECLARE
    row record;
BEGIN
IF (TG_OP = 'UPDATE') THEN
        EXECUTE 'SELECT historize_view($$s_user_ports$$::text, $$t_users_id$$::text, ' || OLD.t_users_id::text || '::text )';
        FOR row IN SELECT t_user_ports_id FROM s_user_ports WHERE t_users_id = OLD.t_users_id LOOP
            EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$t_user_ports_id$$::regclass::oid, ' || row.t_user_ports_id || ', $$UPDATE$$)';
        END LOOP;
END IF;
RETURN NEW;
END;
$t$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_users_t_users_ports_update ON t_users;
CREATE TRIGGER t_users_t_users_ports_update
BEFORE UPDATE
ON t_users
FOR EACH ROW
WHEN (OLD.unix_id IS DISTINCT FROM NEW.unix_id)
EXECUTE PROCEDURE t_users_historize_s_user_ports_trigger();

DROP FUNCTION IF EXISTS t_user_ports_historize_s_user_ports_trigger();
CREATE OR REPLACE FUNCTION t_user_ports_historize_s_user_ports_trigger()
RETURNS TRIGGER
AS $t$
DECLARE
    row record;
BEGIN
IF (TG_OP = 'UPDATE') THEN
        EXECUTE 'SELECT historize_view($$s_user_ports$$::text, $$t_user_ports_id$$::text, ' || OLD.t_user_ports_id::text || '::text )';
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_user_ports$$::regclass::oid, ' || NEW.t_user_ports_id || ', $$UPDATE$$)';
        RETURN NEW;
ELSIF (TG_OP = 'DELETE') THEN
        EXECUTE 'SELECT historize_view($$s_user_ports$$::text, $$t_user_ports_id$$::text, ' || OLD.t_user_ports_id::text || '::text )';
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_user_ports$$::regclass::oid, ' || OLD.t_user_ports_id || ', $$DELETE$$)';
        RETURN OLD;
ELSIF (TG_OP = 'INSERT') THEN
        EXECUTE 'INSERT INTO t_change_log (table_ref, data_id, event_type) VALUES($$s_user_ports$$::regclass::oid, ' || NEW.t_user_ports_id || ', $$INSERT$$)';
        RETURN NEW;
END IF;
END;
$t$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;

DROP TRIGGER IF EXISTS t_user_ports_s_users_ports_update ON t_user_ports;
CREATE TRIGGER t_user_ports_s_users_ports_update
BEFORE UPDATE
ON t_user_ports
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE PROCEDURE t_user_ports_historize_s_user_ports_trigger();

DROP TRIGGER IF EXISTS t_user_ports_s_users_ports_delete ON t_user_ports;
CREATE TRIGGER t_user_ports_s_users_ports_delete
BEFORE DELETE
ON t_user_ports
FOR EACH ROW
EXECUTE PROCEDURE t_user_ports_historize_s_user_ports_trigger();

DROP TRIGGER IF EXISTS t_user_ports_s_users_ports_insert ON t_user_ports;
CREATE TRIGGER t_user_ports_s_users_ports_insert
AFTER INSERT
ON t_user_ports
FOR EACH ROW
EXECUTE PROCEDURE t_user_ports_historize_s_user_ports_trigger();


CREATE OR REPLACE VIEW services.s_services AS
SELECT t_services.t_services_id, t_services.service_type, t_services.info, 
t_services.active, t_services.public, t_addresses.ip_address,
vhostdomaincat(t_addresses.name, t_domains.name) as address, t_addresses6.ip_address as ip6_address
FROM t_services
LEFT JOIN t_addresses ON (t_services.t_addresses_id = t_addresses.t_addresses_id)
LEFT JOIN t_addresses AS t_addresses6 ON (t_services.t_v6addresses_id = t_addresses6.t_addresses_id)
JOIN t_domains ON (t_addresses.t_domains_id = t_domains.t_domains_id)
WHERE t_services.active = TRUE;

GRANT SELECT ON services.s_services TO admins;
GRANT SELECT ON services.s_services TO servers;
