
CREATE GROUP users;
CREATE GROUP admins;
CREATE GROUP servers;
GRANT CONNECT ON DATABASE services to admins;
GRANT CONNECT ON DATABASE services to servers;

CREATE SCHEMA services;
alter database services SET search_path TO public,services;

CREATE OR REPLACE FUNCTION public.is_admin(username text) RETURNS bool AS $$
DECLARE
    adm bool;
BEGIN
    FOR adm IN SELECT true
                FROM pg_roles
                JOIN pg_group ON pg_roles.oid IN (SELECT unnest(grolist))
                WHERE groname = 'admins' AND pg_roles.rolname = username LIMIT 1
        LOOP
            RETURN adm;
        END LOOP;
    RETURN false;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.is_admin() TO users;
GRANT EXECUTE ON FUNCTION public.is_admin() TO admins;

CREATE OR REPLACE FUNCTION public.is_admin() RETURNS bool AS $$
DECLARE
    adm bool;
BEGIN
    RETURN public.is_admin(CURRENT_USER);
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.is_admin() TO users;
GRANT EXECUTE ON FUNCTION public.is_admin() TO admins;


-- Function for array comparsions

CREATE OR REPLACE FUNCTION public.compare_arrays(first text[], second text[])
    RETURNS SETOF text
    AS $$
DECLARE
    retval text;
BEGIN
    FOR retval IN SELECT a.a FROM (SELECT unnest(first::text[]) as a) as a
               LEFT JOIN (select a from unnest(second::text[]) as a) as b using(a) WHERE b.a is null AND a.a IS NOT NULL LOOP
               RETURN NEXT retval;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;
GRANT EXECUTE ON FUNCTION public.compare_arrays(text[], text[]) TO users;
GRANT EXECUTE ON FUNCTION public.compare_arrays(text[], text[]) TO admins;

CREATE OR REPLACE FUNCTION public.last_elem (text[]) RETURNS text AS $$
 SELECT $1[array_length($1,1)];
$$ LANGUAGE SQL;

GRANT EXECUTE ON FUNCTION public.last_elem(text[]) TO users;
GRANT EXECUTE ON FUNCTION public.last_elem(text[]) TO admins;

/*
-- array reverse function ( currently not used )
CREATE OR REPLACE FUNCTION array_reverse(anyarray) RETURNS anyarray AS $$
SELECT ARRAY(
    SELECT $1[i]
    FROM generate_subscripts($1,1) AS s(i)
    ORDER BY i DESC
);
$$ LANGUAGE 'sql' STRICT IMMUTABLE;
*/

CREATE OR REPLACE FUNCTION public.vhostdomaincat(vhost text, domain text) RETURNS text AS $$
  BEGIN
    IF vhost IS NULL OR vhost = '' THEN
      RETURN domain;
    END IF;
    IF domain IS NULL OR domain = '' THEN
      RETURN vhost;
    ELSE
      RETURN vhost || '.' || domain;
    END IF;
  END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.vhostdomaincat(text,text) TO admins;
GRANT EXECUTE ON FUNCTION public.vhostdomaincat(text,text) TO users;

-- Join domain and mailbox name
CREATE OR REPLACE FUNCTION public.emaildomaincat(name text, domain text) RETURNS text AS $$
  BEGIN
    IF name IS NULL OR name = '' THEN
      RETURN NULL;
    END IF;
    IF domain IS NULL OR domain = '' THEN
      RETURN NULL;
    ELSE
      RETURN name || '@' || domain;
    END IF;
  END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.emaildomaincat(text,text) TO admins;
GRANT EXECUTE ON FUNCTION public.emaildomaincat(text,text) TO users;

-- epic funtion to find domain for vhost

-- DROP FUNCTION IF EXISTS find_domain(text);
CREATE OR REPLACE FUNCTION public.find_domain(domain text) RETURNS integer AS $$
    DECLARE
        partarray text[];
        domainpart text;
        r RECORD;
        m text;
        remain text;
        customer_id integer;
    BEGIN
    IF domain IS NULL OR domain = '' THEN
      RETURN -1;
    ELSE
      customer_id := users.t_customers_id FROM users WHERE users.name = CURRENT_USER;
      domainpart = domain;
      partarray = regexp_split_to_array(domain, '\.');
      FOREACH m IN ARRAY partarray
      LOOP
        remain := regexp_replace(domain, '\.?' || domainpart || '$', '');
        FOR r IN SELECT domains.t_domains_id as id, domains.shared as shared
        FROM domains
        WHERE ( domains.t_customers_id = customer_id OR public.is_admin() OR domains.shared = TRUE)
        AND domains.name =  domainpart
        AND (SELECT COUNT(*)
            FROM domains
            WHERE ( domains.t_customers_id = customer_id OR public.is_admin() OR domains.shared = TRUE)
            AND domains.name = domainpart
        ) = 1
        LOOP
            IF r.shared = TRUE THEN
                IF public.require_alias(remain) = TRUE THEN
                    RETURN r.id;
                ELSE
                    RAISE EXCEPTION 'No alias % found for vhost %', remain, domain;
                END IF;
            ELSE
                RETURN r.id;
            END IF;
        END LOOP;
        domainpart = regexp_replace(domainpart, '^' || m || '\.', '');

    END LOOP;
    END IF;
    RAISE EXCEPTION 'Domain for vhost % not found', domain;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.find_domain(text) TO users;
GRANT EXECUTE ON FUNCTION public.find_domain(text) TO admins;


------------------
-- vhost finder --
------------------

-- DROP FUNCTION IF EXISTS find_vhost(text);
CREATE OR REPLACE FUNCTION public.find_vhost(domain text) RETURNS text AS $$
DECLARE
    vhost text;
    t text;
BEGIN
    IF domain IS NULL OR domain = '' THEN
      RAISE EXCEPTION 'No domain given for function find_vhost';
      RETURN NULL;
    ELSE
        FOR vhost IN SELECT domains.name as name FROM domains
                    JOIN users USING(t_customers_id)
                    WHERE domains.t_domains_id = find_domain(domain)
                    AND users.t_customers_id = domains.t_customers_id
                    AND (users.name = CURRENT_USER OR public.is_admin()) LIMIT 1
        LOOP
            t = regexp_replace(domain, '\.?' || vhost || '$', '');
            RETURN t;
        END LOOP;
    END IF;
    RAISE EXCEPTION 'vhost for url % not found', domain;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.find_vhost(text) TO users;
GRANT EXECUTE ON FUNCTION public.find_vhost(text) TO admins;

-- Some mail functions --

-- Find mailbox name from email address.
CREATE OR REPLACE FUNCTION public.mail_name(mail text) RETURNS text AS $$
DECLARE
    domain text;
BEGIN
    IF array_upper(regexp_split_to_array(mail, '@'),1) != 2 THEN
        RAISE EXCEPTION 'Unvalid email address %', mail;
    END IF;
    FOR domain IN SELECT alias[1] as domain
                  FROM regexp_split_to_array(mail, '@') AS alias
                  JOIN domains ON alias[2] = domains.name
                  JOIN users ON domains.t_customers_id = users.t_customers_id
                  WHERE ( users.name = CURRENT_USER OR public.is_admin())
    LOOP
        RETURN domain;
    END LOOP;
    RAISE EXCEPTION 'unkown domain on address %', mail;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.mail_name(text) TO users;
GRANT EXECUTE ON FUNCTION public.mail_name(text) TO admins;


-- find domain from email address
CREATE OR REPLACE FUNCTION public.mail_domain(mail text) RETURNS integer AS $$
DECLARE
    domain text;
    domain_id integer;
BEGIN
    IF array_upper(regexp_split_to_array(mail, '@'),1) != 2 THEN
        RAISE EXCEPTION 'Unvalid email address %', mail;
    END IF;
    FOR domain IN SELECT domains.t_domains_id as domain
                  FROM regexp_split_to_array(mail, '@') AS alias
                  JOIN domains ON alias[2] = domains.name
                  JOIN users ON domains.t_customers_id = users.t_customers_id
                  WHERE ( users.name = CURRENT_USER OR public.is_admin())
    LOOP
        RETURN domain;
    END LOOP;
    RAISE EXCEPTION 'Unknown domain on address %', mail;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.mail_domain(text) TO users;
GRANT EXECUTE ON FUNCTION public.mail_domain(text) TO admins;

/*
-- multi dimersional array
CREATE OR REPLACE FUNCTION  array_agg2(text, text) RETURNS text[]
AS 'select ARRAY[$1::text, $2::text];'
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;
*/
/*
DROP AGGREGATE IF EXISTS array_agg2(text,text);
CREATE AGGREGATE array_agg2(text, text)
(
    sfunc = array_accum,
    stype = text[],
    initcond = '{}'
);
*/

/*
CREATE OR REPLACE FUNCTION array_agg_custom_cut(anyarray)
RETURNS anyarray
    AS 'SELECT $1[2:array_length($1, 1)]'
LANGUAGE SQL IMMUTABLE;

DROP AGGREGATE IF EXISTS array_agg_custom(anyarray);
CREATE AGGREGATE array_agg_custom(anyarray)
(
    SFUNC = array_cat,
    STYPE = anyarray,
    FINALFUNC = array_agg_custom_cut,
    INITCOND = $${{'', ''}}$$
);
*/

CREATE AGGREGATE public.array_accum (anyelement)
(
    sfunc = array_append,
    stype = anyarray,
    initcond = '{}'
);

GRANT EXECUTE ON FUNCTION public.array_accum (anyelement) TO users;
GRANT EXECUTE ON FUNCTION public.array_accum (anyelement) TO admins;


CREATE OR REPLACE FUNCTION unnest_multidim(anyarray)
RETURNS SETOF anyarray AS
$BODY$
  SELECT array_accum($1[series2.i][series2.x]) FROM
    (SELECT generate_series(array_lower($1,2),array_upper($1,2)) as x, series1.i
     FROM
     (SELECT generate_series(array_lower($1,1),array_upper($1,1)) as i) series1
    ) series2
GROUP BY series2.i
$BODY$
LANGUAGE 'sql' IMMUTABLE;

GRANT EXECUTE ON FUNCTION unnest_multidim(anyarray) TO users;
GRANT EXECUTE ON FUNCTION unnest_multidim(anyarray) TO admins;


-- Search first unused port by services_id
CREATE OR REPLACE FUNCTION public.find_free_port(services_id integer)
RETURNS integer
AS $$
DECLARE
    port integer;
    host_id integer;
    lower_limit integer = 40000;
    upper_limit integer = 65536;
BEGIN
    FOR host_id IN SELECT t_services.t_services_id FROM services.t_services
                   WHERE services_id = t_services.t_services_id
                   AND t_services.service_type = 'USER_PORT'
                   LIMIT 1
        LOOP
        FOR port IN SELECT (t_user_ports.port + 1) AS port
                    FROM services.t_user_ports
                    LEFT JOIN t_user_ports AS t_port ON ( t_user_ports.port + 1 ) = t_port.port
                    WHERE t_port.port IS NULL AND t_user_ports.t_services_id = services_id LIMIT 1
            LOOP
                IF port > lower_limit AND port < upper_limit THEN
                    RETURN port;
                END IF;
            END LOOP;
        FOR port IN SELECT (MAX(t_user_ports.port) + 1) as max_port FROM services.t_user_ports WHERE t_user_ports.t_services_id = services_id
                    AND (SELECT (MAX(t_user_ports.port) + 1) FROM services.t_user_ports WHERE t_user_ports.t_services_id = services_id) > lower_limit
                    LIMIT 1
            LOOP
                IF port > lower_limit AND port < upper_limit THEN
                    RETURN port;
                END IF;
                IF port is NULL THEN
                    RETURN lower_limit;
                END IF;
            END LOOP;
        RAISE EXCEPTION 'No free ports found for host %', host;
    END LOOP;
    RAISE EXCEPTION 'Host % not found or you are not allowed to add ports for this host', host;
END;
$$ LANGUAGE plpgsql
-- run as creator
SECURITY DEFINER;
-- If this can be done more securely let me know!

GRANT EXECUTE ON FUNCTION public.find_free_port (integer) TO users;
GRANT EXECUTE ON FUNCTION public.find_free_port (integer) TO admins;

-- Function to create history tables

CREATE OR REPLACE FUNCTION services.create_history_table(tablename text)
RETURNS VOID
AS $$
DECLARE
    historytable text;
    oldcols text;
    cols text;
    col RECORD;
    ttype text;
BEGIN
IF tablename IS NULL OR tablename = '' THEN
    RAISE EXCEPTION 'No table name given';
ELSE
    oldcols := '';
    cols := '';
    ttype := c.relname FROM pg_catalog.pg_class c
            LEFT JOIN pg_catalog.pg_user u ON u.usesysid = c.relowner
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r','')
            AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
            AND pg_catalog.pg_table_is_visible(c.oid)
            AND c.relname = tablename;
    historytable := tablename || '_history';
    EXECUTE 'DROP RULE IF EXISTS ' || tablename || '_delete_historize ON ' || tablename;
    EXECUTE 'DROP RULE IF EXISTS ' || tablename || '_update_historize ON ' || tablename;
    EXECUTE 'DROP FUNCTION IF EXISTS ' || tablename || '_historize(text, text)';
    EXECUTE 'DROP TABLE IF EXISTS ' || historytable;
    EXECUTE 'CREATE TABLE ' || historytable || ' (' || historytable || '_id serial PRIMARY KEY,
            historized timestamptz DEFAULT NOW(), operation event_type,
            old_xmin integer default 0, old_xmax integer default 0)';
    FOR col IN
            SELECT
              a.attnum,
              a.attname AS field,
              t.typname AS type
            FROM
              pg_class c,
              pg_attribute a,
              pg_type t
            WHERE
              c.relname = tablename
              AND a.attnum > 0
              AND a.attrelid = c.oid
              AND a.atttypid = t.oid
              ORDER BY a.attnum
        LOOP
            EXECUTE 'ALTER TABLE ' || historytable || ' ADD COLUMN ' || col.field || ' ' || col.type;
            IF oldcols = '' THEN
                oldcols := 'OLD.' || col.field;
                cols := col.field;
            ELSE
                oldcols := oldcols || ', OLD.' || col.field;
                cols := cols || ', ' || col.field;
            END IF;
        END LOOP;
        IF ttype = 't' THEN
            EXECUTE 'CREATE RULE ' || tablename || '_delete_historize AS ON DELETE TO ' || tablename || ' DO ALSO
                INSERT INTO ' || historytable || ' ( operation, old_xmax, old_xmin, ' || cols || ' ) SELECT
                ' || quote_literal('DELETE') || ', cast(txid_current() as text)::integer,
                cast(OLD.xmin as text)::integer, ' || oldcols;
            EXECUTE 'CREATE RULE ' || tablename || '_update_historize AS ON UPDATE TO ' || tablename || ' DO ALSO
                INSERT INTO ' || historytable || ' ( operation, old_xmax, old_xmin, ' || cols || ' ) SELECT
                ' || quote_literal('UPDATE') || ', cast(txid_current() as text)::integer,
                cast(OLD.xmin as text)::integer, ' || oldcols;
        ELSIF ttype = 'v' THEN
            EXECUTE 'CREATE RULE ' || tablename || '_delete_historize AS ON DELETE TO ' || tablename || ' DO ALSO
                INSERT INTO ' || historytable || ' ( operation, old_xmax, ' || cols || ' ) SELECT
                ' || quote_literal('UPDATE') || ', cast(txid_current() as text)::integer, ' || oldcols;
            EXECUTE 'CREATE RULE ' || tablename || '_update_historize AS ON UPDATE TO ' || tablename || ' DO ALSO
                INSERT INTO ' || historytable || ' ( operation, old_xmax, ' || cols || ' ) SELECT
                ' || quote_literal('UPDATE') || ', cast(txid_current() as text)::integer, ' || oldcols;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS services.historize_view(text,text,text);
CREATE OR REPLACE FUNCTION services.historize_view(viewname text, tkey text, tvalue text)
RETURNS VOID
AS $$
DECLARE
    historytable text;
    colcount integer;
    col RECORD;
    cols text;
    except text;
BEGIN
    historytable := viewname || '_history';
    cols := '';
    colcount := COUNT(a.attname)
                FROM pg_class c, pg_attribute a, pg_type t
                WHERE c.relname = viewname
                AND a.attnum > 0 AND a.attrelid = c.oid AND a.atttypid = t.oid
                AND a.attname = tkey;
    IF colcount = 0 THEN
        --except := 'Column ' || key || ' does not exist in view ' || viewname;
        RAISE EXCEPTION 'Column % does not exist in view % ',tkey,viewname;
    END IF;
    FOR col IN
        SELECT
          a.attnum,
          a.attname AS field,
          t.typname AS type
        FROM
          pg_class c,
          pg_attribute a,
          pg_type t
        WHERE
          c.relname = viewname
          AND a.attnum > 0
          AND a.attrelid = c.oid
          AND a.atttypid = t.oid
          ORDER BY a.attnum
    LOOP
        IF cols = '' THEN
            cols := col.field;
        ELSE
            cols := cols || ', ' || col.field;
        END IF;
    END LOOP;
    colcount := COUNT(a.attnum)
                FROM pg_class c, pg_attribute a, pg_type t
                WHERE c.relname = viewname
                AND a.attnum > 0 AND a.attrelid = c.oid AND a.atttypid = t.oid;
    IF colcount = 0 THEN
        -- create history table
        EXECUTE 'SELECT create_history_table(' || viewname || ')';
    END IF;
    EXECUTE 'INSERT INTO ' || historytable || '(  old_xmax, ' || cols || ' ) SELECT cast(txid_current() as text)::integer, ' || cols || '
            FROM ' || viewname || ' WHERE ' || tkey || ' = ' || tvalue;
END;
$$ LANGUAGE plpgsql;

-- function to create log rules

DROP FUNCTION IF EXISTS services.create_log_triggers(text);
CREATE OR REPLACE FUNCTION services.create_log_triggers(tablen text)
RETURNS VOID
AS $f$
DECLARE
    pk text;
    tablename text;
    tableschema text;
BEGIN
    -- get primary key
    IF array_upper(regexp_split_to_array(tablen::text, '\.')::text[], 1) = 2 THEN
        tableschema := a[1] FROM regexp_split_to_array(tablen::text, '\.') AS a;
        tablename := a[2] FROM regexp_split_to_array(tablen::text, '\.') AS a;
    ELSE
        tablename := tablen::text;
    END IF;
    IF tableschema IS NOT NULL THEN
        pk := c.column_name
          FROM information_schema.table_constraints tc
          JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
          JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
          WHERE constraint_type = 'PRIMARY KEY' and tc.table_name = tablename
          AND tc.constraint_schema = tableschema
          LIMIT 1;
    ELSE
        pk := c.column_name
          FROM information_schema.table_constraints tc
          JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
          JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
          WHERE constraint_type = 'PRIMARY KEY' and tc.table_name = tablename LIMIT 1;
    END IF;
    IF pk IS NULL THEN
        RAISE EXCEPTION 'No primary key found for table %', tablename;
    END IF;
    EXECUTE 'DROP TRIGGER IF EXISTS ' || tablename::text || '_log_insert ON ' || tablen::text;
    EXECUTE 'CREATE TRIGGER ' || tablename::text || '_log_insert
            AFTER INSERT ON ' || tablen::text || '
            FOR EACH ROW
            EXECUTE PROCEDURE log_trigger($$' || pk::text || '$$)';
    EXECUTE 'DROP TRIGGER IF EXISTS ' || tablename::text || '_log_update ON ' || tablen::text;
    EXECUTE 'CREATE TRIGGER ' || tablename::text || '_log_update
            AFTER UPDATE ON ' || tablen::text || '
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE PROCEDURE log_trigger($$' || pk::text || '$$)';
    EXECUTE 'DROP TRIGGER IF EXISTS ' || tablename::text || '_log_delete ON ' || tablen::text;
    EXECUTE 'CREATE TRIGGER ' || tablename::text || '_log_delete
            BEFORE DELETE ON ' || tablen::text || '
            FOR EACH ROW
            EXECUTE PROCEDURE log_trigger($$' || pk::text || '$$)';
END;
$f$ LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS services.log_trigger();
CREATE OR REPLACE function services.log_trigger()
    RETURNS TRIGGER
AS $t$
DECLARE
    pk TEXT;
    t text;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        EXECUTE 'SELECT ($1).' || TG_ARGV[0] || '::text' INTO t USING NEW;
        EXECUTE 'INSERT INTO t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$, $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        EXECUTE 'SELECT ($1).' || TG_ARGV[0] || '::text' INTO t USING NEW;
        EXECUTE 'INSERT INTO t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$ , $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        EXECUTE 'SELECT ($1).' || TG_ARGV[0] || '::text' INTO t USING OLD;
        EXECUTE 'INSERT INTO t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$, $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN OLD;
    END IF;
END;
$t$ LANGUAGE plpgsql
SECURITY DEFINER;

DROP FUNCTION IF EXISTS services.ip_on_subnet(inet, integer);
CREATE FUNCTION services.ip_on_subnet(ip inet, subnet_id integer)
RETURNS BOOLEAN
AS $f$
DECLARE
    isin boolean;
BEGIN
    isin := (t_subnets.address >> ip::inet) FROM t_subnets WHERE t_subnets.t_subnets_id = subnet_id;
    IF isin IS true OR isin IS false THEN
        RETURN isin;
    END IF;
    RAISE EXCEPTION 'Subnet % not found', subnet_id;
END;
$f$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION services.ip_on_subnet(inet, integer) TO admins;

DROP FUNCTION IF EXISTS public.require_alias(text);
CREATE OR REPLACE FUNCTION public.require_alias(aliasname text)
RETURNS BOOLEAN
AS
$f$
DECLARE
    alias text;
BEGIN
    FOR alias IN SELECT customers.t_customers_id
                FROM users JOIN customers USING (t_customers_id) 
                WHERE users.name = CURRENT_USER::text 
                AND aliasname = ANY(customers.aliases) 
        LOOP
        IF alias IS NOT NULL THEN
            RETURN TRUE;
        END IF;
    END LOOP;
    RETURN FALSE;
END;
$f$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.require_alias(text) TO users;
GRANT EXECUTE ON FUNCTION public.require_alias(text) TO admins;



DROP FUNCTION IF EXISTS public.valid_database_name(text);
CREATE OR REPLACE FUNCTION public.valid_database_name(database text)
RETURNS BOOLEAN
AS
$f$
DECLARE
    regex text;
    isvalid boolean;
    alias text;
BEGIN
    regex := '^' || CURRENT_USER::text || '(_[a-z0-9_]+)?$';
    isvalid := database ~* regex;
    IF isvalid = TRUE THEN
        RETURN TRUE;
    END IF;
    FOR alias IN SELECT DISTINCT unnest(aliases) as alias 
                FROM users JOIN customers USING (t_customers_id) 
                WHERE users.name = CURRENT_USER::text LOOP
        IF alias IS NOT NULL THEN
            regex := '^' || alias || '(_[a-z0-9_]+)?$';
            isvalid := database ~* regex;
            IF isvalid = TRUE THEN
                RETURN TRUE;
            END IF;
        END IF;
    END LOOP;
    RETURN FALSE;
END;
$f$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.valid_database_name(text) TO users;
GRANT EXECUTE ON FUNCTION public.valid_database_name(text) TO admins;

--
-- Functios end
--

-- CREATE TYPES --

CREATE TYPE t_change_log_event_type AS ENUM ('INSERT', 'UPDATE', 'DELETE');
CREATE type domain_type AS enum ('MASTER', 'SLAVE', 'NONE');
CREATE TYPE event_type AS ENUM ('INSERT','UPDATE', 'DELETE');
CREATE TYPE t_hosts_type AS ENUM ('HARDWARE', 'VIRTUAL');
--CREATE TYPE service_category AS ENUM ('DATABASE', 'MAIL', 'WWW', 'SHELL', 'OTHER');
--CREATE TYPE service_type AS ENUM ('VHOST','MAIL','MAILLIST','JABBER','WORDPRESS','USER_PORTS','SHELL','POSTGRESQL','MYSQL');

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

COMMENT ON COLUMN t_change_log.event_type IS 'INSERT, UPDATE, DELETE';
GRANT USAGE ON t_change_log_t_change_log_id_seq to users;

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

SELECT services.create_log_triggers('services.t_customers');

-- mainly for Kapsi's needs

CREATE TABLE services.t_aliases
(
    t_aliases_id serial NOT NULL PRIMARY KEY,
    t_customers_id integer references t_customers NOT NULL,
    alias text NOT NULL UNIQUE
);

SELECT create_log_triggers('services.t_aliases');

GRANT SELECT,UPDATE,INSERT,DELETE ON services.t_aliases TO admins;
GRANT USAGE ON services.t_aliases_t_aliases_id_seq TO admins;


-- DOMAINS

CREATE TABLE services.t_domains (
    t_domains_id serial NOT NULL PRIMARY KEY,
    name text UNIQUE NOT NULL,
    shared boolean DEFAULT false NOT NULL,
    t_customers_id integer,
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

SELECT create_log_triggers('services.t_domains');

ALTER TABLE t_domains ADD CONSTRAINT "domains_check" CHECK (
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

ALTER TABLE t_domains ADD CONSTRAINT "valid_admin_address" CHECK (
    admin_address ~ '^[^@\s]+@[^@\s]+(\.[^@\s]+)+$');

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

SELECT create_log_triggers('services.t_dns_keys');

-- USERS

CREATE TABLE services.t_users (
    t_users_id serial NOT NULL PRIMARY KEY,
    t_customers_id integer NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    name text NOT NULL UNIQUE,
    lastname text,
    firstnames text,
    phone text,
    unix_id integer UNIQUE,
    password_changed timestamp with time zone DEFAULT now() NOT NULL,
    t_domains_id integer references t_domains NOT NULL
);

GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_users TO admins;

SELECT create_log_triggers('services.t_users');

CREATE OR REPLACE VIEW public.users AS
    SELECT t_users.t_customers_id, t_users.name, t_users.lastname, t_users.firstnames, t_users.phone,
    t_users.unix_id, t_users.t_users_id, t_users.t_domains_id, public.is_admin(t_users.name) as admin
    FROM services.t_users
    WHERE (t_users.name = ("current_user"())::text OR public.is_admin());

GRANT SELECT ON public.users TO users;
GRANT SELECT ON public.users TO admins;

CREATE OR REPLACE VIEW public.customers AS
SELECT t_customers.t_customers_id, t_customers.name, array_agg(distinct t_aliases.alias) as aliases
FROM t_customers
JOIN t_users USING (t_customers_id)
LEFT JOIN t_aliases USING (t_customers_id)
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
FROM t_domains
JOIN t_customers USING (t_customers_id)
JOIN t_users USING (t_customers_id)
WHERE ((( t_users.name = "current_user"()::text AND public.is_admin() IS FALSE) OR t_domains.shared = TRUE ) OR public.is_admin())
-- if there many users in one customers
GROUP BY t_domains.t_domains_id;

CREATE OR REPLACE RULE domains_insert
AS ON INSERT TO public.domains
DO INSTEAD
INSERT INTO t_domains
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
FROM t_customers, t_users
WHERE t_domains.t_domains_id = new.t_domains_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (( t_users.name = CURRENT_USER AND NOT public.is_admin()) OR public.is_admin());

CREATE OR REPLACE RULE domains_delete
AS ON DELETE TO domains
DO INSTEAD
DELETE FROM t_domains USING t_customers, t_users
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
ALTER TABLE public.domains ALTER domain_type SET DEFAULT 'master';
ALTER TABLE public.domains ALTER admin_address SET DEFAULT 'hostmaster@example.com';

GRANT SELECT,INSERT,UPDATE,DELETE ON domains TO users;
GRANT SELECT,INSERT,UPDATE,DELETE ON domains TO admins;
GRANT USAGE ON services.t_domains_t_domains_id_seq TO users;
GRANT USAGE ON services.t_domains_t_domains_id_seq TO admins;

-------------
-- subnets --
-------------

CREATE TABLE services.t_subnets
(   t_subnets_id serial NOT NULL PRIMARY KEY,
    name text NOT NULL UNIQUE,
    location text NOT NULL,
    info text,
    vlan_tag integer NOT NULL DEFAULT 0,
    address inet NOT NULL,
    gateway inet,
    dns_servers inet[],
    dhcp_range inet,
    dhcp_options text,
    mtu integer NOT NULL default 1500,
    hostmaster_address text NOT NULL DEFAULT 'hostmaster@example.com'::text
);

ALTER TABLE services.t_subnets ADD CONSTRAINT "vlan_tag_check" CHECK (vlan_tag >= 0 AND vlan_tag <= 65536);
ALTER TABLE services.t_subnets ADD CONSTRAINT "valid mtu" CHECK (mtu >= 0 AND mtu <= 15500);

SELECT create_log_triggers('services.t_subnets');

------------------------------
-- Hosts aka. computers etc --
------------------------------

CREATE TABLE services.t_hosts
(
    t_hosts_id serial NOT NULL PRIMARY KEY,
    name text NOT NULL UNIQUE,
    type t_hosts_type NOT NULL DEFAULT 'VIRTUAL',
    t_domains_id integer references t_domains,
    t_customers_id integer references t_customers,
    location text NOT NULL DEFAULT ''
);

ALTER TABLE services.t_hosts ADD CONSTRAINT valid_name CHECK (name ~* '^[a-z0-9]+$');
ALTER TABLE services.t_hosts ADD UNIQUE (name, t_domains_id);

SELECT services.create_log_triggers('t_hosts');

----------------
-- Interfaces --
----------------
-- Interfaces and addresses on computers

CREATE TABLE services.t_addresses
(
    t_addresses_id serial PRIMARY KEY NOT NULL,
    t_subnets_id integer references t_subnets NOT NULL,
    ip_address inet NOT NULL,
    t_domains_id integer references t_domains NOT NULL,
    name text NOT NULL,
    t_hosts_id integer REFERENCES t_hosts NOT NULL,
    info text,
    active boolean NOT NULL DEFAULT true,
    mac_address macaddr -- optional
);

ALTER TABLE services.t_addresses ADD UNIQUE (t_domains_id, name);
ALTER TABLE services.t_addresses ADD CONSTRAINT valid_name CHECK (name ~* '^[a-z0-9\-\._]*$');
ALTER TABLE services.t_addresses ADD CONSTRAINT valid_ip CHECK (services.ip_on_subnet(ip_address::inet, t_subnets_id::integer));
GRANT USAGE ON services.t_addresses_t_addresses_id_seq TO admins;
GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_addresses TO admins;
GRANT SELECT ON services.t_addresses TO servers;

SELECT create_log_triggers('services.t_addresses');

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

SELECT create_log_triggers('services.t_services');

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

------------
-- VHOSTS --
------------

CREATE TABLE services.t_vhosts
(
    t_vhosts_id serial not null PRIMARY KEY,
    t_users_id integer REFERENCES t_users NOT NULL,
    parent_id integer REFERENCES t_vhosts,
    www_servers_id integer REFERENCES t_hosts,
    name text not null,
    created timestamptz default now(),
    t_domains_id integer not null REFERENCES t_domains,
    is_redirect boolean default false not null,
    logaccess boolean default false not null,
    redirect_to text default null,
    locked boolean default false not null,
    CONSTRAINT valid_redirect CHECK (
        (
            redirect_to IS NULL
            OR (redirect_to ~* '^https?://'::text AND NOT is_redirect)
        )
        OR
        (
            redirect_to IS NULL
            AND is_redirect
        )),
    CONSTRAINT valid_name CHECK (name ~* '^[a-z0-9\.\-]*$')
);

ALTER TABLE services.t_vhosts add unique(t_domains_id, name);

SELECT create_log_triggers('services.t_vhosts');

CREATE OR REPLACE VIEW public.vhosts
AS
SELECT t_vhosts.t_vhosts_id, t_customers.t_customers_id, t_users.name as username, t_vhosts.t_users_id, t_vhosts.created,
vhostdomaincat(t_vhosts.name, t_dom.name::text) as name,
array_agg(distinct vhostdomaincat(t_vhost_aliases.name::text,t_aliases_domains.name::text)::text) as aliases,
array_agg(distinct vhostdomaincat(t_vhost_redirects.name::text,t_redirects_domains.name::text)::text) as redirects,
t_vhosts.redirect_to,
t_vhosts.logaccess,
t_vhosts.locked,
t_dom.t_domains_id
FROM t_vhosts
JOIN t_domains as t_dom ON (t_vhosts.t_domains_id = t_dom.t_domains_id)
JOIN t_users ON (t_users.t_users_id = t_vhosts.t_users_id)
JOIN t_customers ON (t_users.t_customers_id = t_customers.t_customers_id)
LEFT JOIN t_vhosts AS t_vhost_aliases ON (t_vhosts.t_vhosts_id = t_vhost_aliases.parent_id
    AND NOT t_vhost_aliases.is_redirect
    AND t_vhost_aliases.redirect_to IS NULL
    AND t_vhost_aliases.t_users_id = t_users.t_users_id)
LEFT JOIN t_vhosts AS t_vhost_redirects ON (t_vhosts.t_vhosts_id = t_vhost_redirects.parent_id
    AND t_vhost_redirects.is_redirect
    AND t_vhost_redirects.redirect_to IS NULL
    AND t_vhost_redirects.t_users_id = t_users.t_users_id)
LEFT JOIN t_domains AS t_aliases_domains ON (t_aliases_domains.t_domains_id = t_vhost_aliases.t_domains_id)
LEFT JOIN t_domains AS t_redirects_domains ON (t_redirects_domains.t_domains_id = t_vhost_redirects.t_domains_id)
WHERE t_vhosts.parent_id IS NULL
AND  (t_users.name = CURRENT_USER OR public.is_admin())
AND t_users.t_customers_id = t_customers.t_customers_id
GROUP BY t_vhosts.t_vhosts_id,t_dom.name,t_customers.t_customers_id,t_users.name,t_dom.t_domains_id;

ALTER TABLE public.vhosts ALTER COLUMN logaccess SET DEFAULT false;
ALTER TABLE public.vhosts ALTER COLUMN created SET DEFAULT NOW();
ALTER TABLE public.vhosts ALTER COLUMN locked SET DEFAULT false;

GRANT SELECT ON public.vhosts TO users;

CREATE OR REPLACE VIEW public.vhost_aliases
AS
SELECT t_vhosts.t_vhosts_id, t_vhosts.t_users_id, t_customers.t_customers_id,
vhostdomaincat(t_vhosts.name, t_domains.name::text) as name,
t_domains.t_domains_id,
t_vhosts.parent_id
FROM t_vhosts
JOIN t_domains ON (t_vhosts.t_domains_id = t_domains.t_domains_id)
JOIN t_users ON (t_vhosts.t_users_id = t_users.t_users_id)
JOIN t_customers ON (t_users.t_customers_id = t_customers.t_customers_id)
WHERE t_vhosts.parent_id IS NOT NULL
AND  (t_users.name = CURRENT_USER OR public.is_admin())
AND NOT t_vhosts.is_redirect
AND t_vhosts.redirect_to IS NULL;

GRANT SELECT ON public.vhost_aliases TO users;

CREATE OR REPLACE VIEW public.vhost_redirects
AS
SELECT t_vhosts.t_vhosts_id, t_vhosts.t_users_id, t_customers.t_customers_id,
vhostdomaincat(t_vhosts.name, t_domains.name::text) as name,
t_domains.t_domains_id,
t_vhosts.parent_id
FROM t_vhosts
JOIN t_domains ON (t_vhosts.t_domains_id = t_domains.t_domains_id)
JOIN t_users ON (t_vhosts.t_users_id = t_users.t_users_id)
JOIN t_customers ON (t_users.t_customers_id = t_customers.t_customers_id)
WHERE t_vhosts.parent_id IS NOT NULL
AND  (t_users.name = CURRENT_USER OR public.is_admin())
AND (t_vhosts.is_redirect
OR t_vhosts.redirect_to IS NOT NULL);

GRANT SELECT ON public.vhost_redirects TO users;

CREATE OR REPLACE RULE vhosts_insert
AS ON INSERT TO public.vhosts
DO INSTEAD
(
INSERT INTO t_vhosts
(t_users_id, name, t_domains_id, redirect_to,logaccess,locked)
SELECT users.t_users_id,
find_vhost(NEW.name),
find_domain(NEW.name),
NEW.redirect_to,
(public.is_admin() AND NEW.logaccess),
(public.is_admin() AND NEW.locked)
FROM users
JOIN t_customers USING (t_customers_id)
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
-- Limit vhost count to something sane
AND (
    SELECT COUNT(vhosts.t_vhosts_id)
    FROM vhosts, users
    WHERE users.name = CURRENT_USER
    AND vhosts.username = users.name
) < 50
-- don't insert without aliases
RETURNING t_vhosts_id, (SELECT users.t_customers_id FROM users WHERE users.t_users_id = t_vhosts.t_users_id) AS t_customers_id,
(SELECT users.name from users WHERE users.t_users_id = t_vhosts.t_users_id), t_vhosts.t_users_id,
    t_vhosts.created, (SELECT vhostdomaincat(t_vhosts.name, domains.name) FROM domains WHERE domains.t_domains_id = t_vhosts.t_domains_id),
    ARRAY[]::text[], ARRAY[]::text[], t_vhosts.redirect_to, t_vhosts.logaccess,t_vhosts.locked,t_vhosts.t_domains_id;
-- add aliases also
INSERT INTO t_vhosts (t_users_id, t_domains_id, name, parent_id)
SELECT users.t_users_id,
find_domain(unnest(new.aliases)) as domain,
find_vhost(unnest(new.aliases)) as name,
vhosts.t_vhosts_id
FROM users
JOIN t_customers USING (t_customers_id)
JOIN vhosts USING (t_users_id)
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
AND vhosts.name = NEW.name
;
INSERT INTO t_vhosts (t_users_id, t_domains_id, name, parent_id, is_redirect)
SELECT users.t_users_id,
find_domain(unnest(new.redirects)) as domain,
find_vhost(unnest(new.redirects)) as name,
vhosts.t_vhosts_id,
true
FROM users
JOIN t_customers USING (t_customers_id)
JOIN vhosts USING (t_users_id)
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
AND vhosts.name = NEW.name
;
);

GRANT INSERT ON public.vhosts TO users;
GRANT USAGE ON t_vhosts_t_vhosts_id_seq TO users;

CREATE OR REPLACE RULE vhosts_update
AS ON UPDATE TO vhosts
DO INSTEAD
( UPDATE t_vhosts
SET
redirect_to = NEW.redirect_to,
logaccess = (public.is_admin() AND NEW.logaccess),
locked = (public.is_admin() AND NEW.locked)
FROM t_customers, users
WHERE t_vhosts.t_vhosts_id = new.t_vhosts_id
AND old.t_users_id = users.t_users_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_users_id = OLD.t_users_id))
RETURNING t_vhosts_id, (SELECT users.t_customers_id FROM users WHERE users.t_users_id = t_vhosts.t_users_id) AS t_customers_id,
(SELECT users.name from users WHERE users.t_users_id = t_vhosts.t_users_id), t_vhosts.t_users_id,
    t_vhosts.created, (SELECT vhostdomaincat(t_vhosts.name, domains.name) FROM domains WHERE domains.t_domains_id = t_vhosts.t_domains_id),
    ARRAY[]::text[], ARRAY[]::text[], t_vhosts.redirect_to, t_vhosts.logaccess,t_vhosts.locked,t_vhosts.t_domains_id;
-- delete removed alias row from t_vhost_aliases table
DELETE FROM t_vhosts
WHERE parent_id = old.t_vhosts_id
AND (
    t_vhosts_id IN (
    SELECT vhost_aliases.t_vhosts_id
    FROM vhost_aliases
    WHERE vhost_aliases.name IN (
        SELECT compare_arrays(old.aliases::text[], new.aliases::text[])
        )
    )
    OR t_vhosts_id IN
    (
        SELECT vhost_redirects.t_vhosts_id
        FROM vhost_redirects
        WHERE vhost_redirects.name IN (
            SELECT compare_arrays(old.redirects::text[], new.redirects::text[])
        )
    )
);
INSERT INTO t_vhosts (t_users_id, parent_id, name, t_domains_id, is_redirect)
SELECT users.t_users_id,  old.t_vhosts_id,
find_vhost(compare_arrays(new.aliases::text[], old.aliases::text[])) as name,
find_domain(compare_arrays(new.aliases::text[], old.aliases::text[])) as t_domains_id,
false
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_users_id = OLD.t_users_id));
INSERT INTO t_vhosts (t_users_id, parent_id, name, t_domains_id, is_redirect)
SELECT users.t_users_id,  old.t_vhosts_id,
find_vhost(compare_arrays(new.redirects::text[], old.redirects::text[])) as name,
find_domain(compare_arrays(new.redirects::text[], old.redirects::text[])) as t_domains_id,
true
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_users_id = OLD.t_users_id));
);

GRANT UPDATE ON public.vhosts TO users;

CREATE OR REPLACE RULE vhosts_delete
AS ON DELETE TO vhosts
DO INSTEAD
(
DELETE FROM t_vhosts USING t_customers, t_users
WHERE t_vhosts.parent_id = OLD.t_vhosts_id
AND old.t_users_id = t_users.t_users_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (t_users.name = CURRENT_USER  OR public.is_admin())
--LIMIT 50
;
DELETE FROM t_vhosts USING t_customers, t_users
WHERE t_vhosts.t_vhosts_id = OLD.t_vhosts_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (t_users.name = CURRENT_USER OR public.is_admin())
--LIMIT 50
;
);

GRANT DELETE ON public.vhosts TO users;


-- ------------
-- Mailboxes --
-- ------------

CREATE TABLE services.t_mailboxes
(
    t_mailboxes_id serial PRIMARY KEY NOT NULL,
    t_domains_id integer references t_domains NOT NULL,
    name text NOT NULL,
    t_customers_id integer references t_customers NOT NULL,
    created timestamptz DEFAULT NOW() NOT NULL
);

ALTER TABLE t_mailboxes ADD UNIQUE(t_domains_id,name);
ALTER TABLE t_mailboxes ADD CONSTRAINT valid_name CHECK (lower(name) ~* $t$^[a-z0-9\.!#$%&'*+-/=?^_`{|}~]+$$t$);

GRANT SELECT,INSERT,UPDATE,DELETE ON services.t_mailboxes TO admins;

CREATE TABLE services.t_mail_aliases (
    t_mail_aliases_id serial NOT NULL PRIMARY KEY,
    t_domains_id integer NOT NULL REFERENCES services.t_domains,
    name text NOT NULL,
    t_mailboxes_id integer NOT NULL REFERENCES services.t_mailboxes,
    t_customers_id integer NOT NULL REFERENCES services.t_customers
);

ALTER TABLE t_mail_aliases ADD CONSTRAINT valid_name CHECK (lower(name) ~* $t$^[a-z0-9\.!#$%&'*+-/=?^_`{|}~]+$$t$);

SELECT create_log_triggers('services.t_mail_aliases');
SELECT create_log_triggers('services.t_mailboxes');

DROP VIEW public.mailboxes;
CREATE OR REPLACE VIEW public.mailboxes
AS
SELECT t_mailboxes.t_mailboxes_id, t_mailboxes.name || '@' || t_domain_mail.name as name, t_mailboxes.t_customers_id, t_mailboxes.created,
array_agg(t_mail_aliases.name || '@' || t_domains.name) AS aliases, t_domain_mail.t_domains_id
  FROM t_mailboxes
  JOIN t_customers USING (t_customers_id)
  JOIN t_users USING (t_customers_id)
  JOIN t_domains as t_domain_mail ON t_mailboxes.t_domains_id = t_domain_mail.t_domains_id
  LEFT JOIN t_mail_aliases USING (t_mailboxes_id)
  LEFT JOIN t_domains ON t_mail_aliases.t_domains_id = t_domains.t_domains_id
 WHERE (t_users.name = CURRENT_USER OR public.is_admin())
 GROUP BY t_mailboxes.t_mailboxes_id, t_domain_mail.t_domains_id, t_domain_mail.t_domains_id;

GRANT SELECT ON mailboxes TO users;
GRANT SELECT ON mailboxes TO admins;

CREATE OR REPLACE VIEW public.mail_aliases AS
SELECT t_mail_aliases.t_mail_aliases_id, t_mail_aliases.t_customers_id, t_mail_aliases.t_mailboxes_id,
emaildomaincat(t_mail_aliases.name, t_domains.name::text) AS alias,
t_domains.t_domains_id
FROM t_mail_aliases
JOIN t_domains on t_mail_aliases.t_domains_id = t_domains.t_domains_id
JOIN t_users ON t_mail_aliases.t_customers_id =  t_users.t_customers_id
WHERE (t_users.name = CURRENT_USER OR public.is_admin());

GRANT SELECT ON public.mail_aliases TO users;
GRANT SELECT ON public.mail_aliases TO admins;

CREATE OR REPLACE RULE mailboxes_insert
AS ON INSERT TO public.mailboxes
DO INSTEAD
( SELECT nextval('t_mailboxes_t_mailboxes_id_seq'::regclass);
INSERT INTO t_mailboxes
(t_mailboxes_id, t_customers_id, t_domains_id, name)
SELECT currval('t_mailboxes_t_mailboxes_id_seq'::regclass), users.t_customers_id,
public.mail_domain(NEW.name) as mail_domain, public.mail_name(NEW.name) as name
FROM users, domains
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = NEW.t_customers_id))
AND public.mail_domain(NEW.name) = domains.t_domains_id
AND domains.t_customers_id = users.t_customers_id
AND (
    SELECT COUNT(mailboxes.t_mailboxes_id)
    FROM mailboxes, users
    WHERE users.name = CURRENT_USER
    AND mailboxes.t_customers_id = users.t_customers_id
    ) < 50
RETURNING t_mailboxes_id as t_mailboxes_id, name as name, t_customers_id as t_customers_id, created as created,
ARRAY[]::text[] as aliases, t_domains_id;
INSERT INTO t_mail_aliases
(t_customers_id, t_domains_id, name, t_mailboxes_id)
SELECT users.t_customers_id, mail_domain(unnest(NEW.aliases)) as mail_domain,
mail_name(unnest(NEW.aliases)), currval('t_mailboxes_t_mailboxes_id_seq'::regclass)
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = NEW.t_customers_id))
-- RETURNING t_customers_id, t_domains_id, t_mail_aliases.name, t_mailboxes_id
;
);

GRANT INSERT on mailboxes TO users;
GRANT INSERT on mailboxes TO admins;
GRANT USAGE ON t_mailboxes_t_mailboxes_id_seq to users;
GRANT USAGE ON t_mail_aliases_t_mail_aliases_id_seq TO users;
GRANT USAGE ON t_mailboxes_t_mailboxes_id_seq to admins;
GRANT USAGE ON t_mail_aliases_t_mail_aliases_id_seq TO admins;

CREATE OR REPLACE RULE mailboxes_update
AS ON UPDATE TO public.mailboxes
DO INSTEAD
( UPDATE t_mailboxes
SET
t_domains_id = public.mail_domain(NEW.name),
name = public.mail_name(NEW.name)
FROM t_customers, users, t_domains
WHERE t_mailboxes.t_mailboxes_id = new.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_domains.t_customers_id = users.t_customers_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id));
-- delete removed alias row from t_vhost_aliases table
DELETE FROM t_mail_aliases
WHERE t_mail_aliases.t_mailboxes_id = old.t_mailboxes_id
AND t_mail_aliases.t_mail_aliases_id IN (
    SELECT mail_aliases.t_mail_aliases_id
    FROM mail_aliases
    WHERE mail_aliases.alias IN (
        SELECT compare_arrays(old.aliases::text[], new.aliases::text[])
    )
);
INSERT INTO t_mail_aliases (t_customers_id, t_mailboxes_id, name, t_domains_id)
SELECT users.t_customers_id,  old.t_mailboxes_id,
mail_name(compare_arrays(new.aliases::text[], old.aliases::text[])) as name,
mail_domain(compare_arrays(new.aliases::text[], old.aliases::text[])) as t_domains_id
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id))
);

GRANT UPDATE on mailboxes TO users;
GRANT UPDATE on mailboxes TO admins;

CREATE OR REPLACE RULE mailboxes_delete
AS ON DELETE TO mailboxes
DO INSTEAD
(
DELETE FROM t_mail_aliases USING t_customers, t_users
WHERE t_mail_aliases.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
-- LIMIT 50
;
DELETE FROM t_mailboxes USING t_customers, t_users
WHERE t_mailboxes.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
-- LIMIT 50
;
);

GRANT DELETE on mailboxes TO users;
GRANT DELETE on mailboxes TO admins;

------------------
-- IP-addresses --
------------------
/*
-- WTF??
-- Same as t_interfaces maybe
CREATE TABLE services.t_ip_addresses
(
    t_ip_addresses_id serial NOT NULL PRIMARY KEY,
    t_hosts_id integer references t_hosts,
    address inet NOT NULL,
    name text NOT NULL,
    t_domains_id integer references t_domains,
    t_customers_id integer references t_customers,
    t_subnets_id integer references t_subnets NOT NULL,
    info text
);

ALTER TABLE t_ip_addresses ADD UNIQUE (address, t_subnets_id);
ALTER TABLE t_ip_addresses ADD CONSTRAINT valid_name CHECK (name ~* '^([a-z0-9]+\.?[a-z0-9])+$');

SELECT services.create_log_triggers('t_ip_addersses');

*/
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

SELECT services.create_log_triggers('services.t_user_ports');

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
SELECT services.create_log_triggers('services.t_databases');

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
FROM t_vhosts
JOIN t_domains as t_dom ON (t_vhosts.t_domains_id = t_dom.t_domains_id)
JOIN t_users ON (t_users.t_users_id = t_vhosts.t_users_id)
JOIN t_customers ON (t_users.t_customers_id = t_customers.t_customers_id)
LEFT JOIN t_vhosts AS t_vhost_aliases ON (t_vhosts.t_vhosts_id = t_vhost_aliases.parent_id
    AND NOT t_vhost_aliases.is_redirect
    AND t_vhost_aliases.redirect_to IS NULL
    AND t_vhost_aliases.t_users_id = t_users.t_users_id)
LEFT JOIN t_vhosts AS t_vhost_redirects ON (t_vhosts.t_vhosts_id = t_vhost_redirects.parent_id
    AND t_vhost_redirects.is_redirect
    AND t_vhost_redirects.redirect_to IS NULL
    AND t_vhost_redirects.t_users_id = t_users.t_users_id)
LEFT JOIN t_domains AS t_aliases_domains ON (t_aliases_domains.t_domains_id = t_vhost_aliases.t_domains_id)
LEFT JOIN t_domains AS t_redirects_domains ON (t_redirects_domains.t_domains_id = t_vhost_redirects.t_domains_id)
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
BEFORE UPDATE OR DELETE
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
(t_addresses.name || '.'::text) || t_domains.name AS server, t_addresses.t_hosts_id as t_hosts_id
FROM t_user_ports
JOIN t_users USING (t_users_id)
JOIN t_customers ON t_users.t_customers_id = t_customers.t_customers_id
JOIN t_services USING (t_services_id)
JOIN t_addresses ON (t_services.t_addresses_id = t_addresses.t_addresses_id)
JOIN t_domains ON t_addresses.t_domains_id = t_domains.t_domains_id
WHERE t_user_ports.t_services_id = t_services.t_services_id;

GRANT SELECT ON services.s_user_ports TO servers;
GRANT SELECT ON services.s_user_ports TO admins;

SELECT create_history_table('s_user_ports'::text);
ALTER TABLE s_user_ports_history SET SCHEMA services;
GRANT SELECT ON services.s_user_ports_history TO servers;
GRANT SELECT ON services.s_user_ports_history TO admins;

DROP FUNCTION t_users_historize_s_user_ports_trigger();
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

-----------------------
-- CREATE SOME USERS --
-----------------------

-- normal user
CREATE USER username NOCREATEDB NOINHERIT IN GROUP users;

-- admin
CREATE USER admin NOCREATEDB NOINHERIT IN GROUP admins;
GRANT USAGE ON SCHEMA services TO admin;