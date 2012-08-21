
-- public.is_admin (text) function
-- username given as argument
-- check if username is in admins postgresql user group
-- returns true if username is admin user, false if not

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

-- do users really need this??
GRANT EXECUTE ON FUNCTION public.is_admin(text) TO users;
GRANT EXECUTE ON FUNCTION public.is_admin(text) TO admins;
GRANT EXECUTE ON FUNCTION public.is_admin(text) TO servers;


-- public.is_admin () function
-- check if logged user is in admins postgresql user group
-- returns true if user is admin user, false if not
-- uses public.is_admin(text) function
-- CAUTION: This function is used to determine what
-- rows user can view, if this function fails, views
-- won't work properly

CREATE OR REPLACE FUNCTION public.is_admin() RETURNS bool AS $$
DECLARE
    adm bool;
BEGIN
    RETURN public.is_admin(CURRENT_USER);
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.is_admin() TO users;
GRANT EXECUTE ON FUNCTION public.is_admin() TO admins;
GRANT EXECUTE ON FUNCTION public.is_admin() TO servers;


-- Function for array comparsions
-- Compares given arrays and returns new lines on first array
-- Simple one way diff, if you need removed rows switch first and second array

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

-- It's needed by users and admins and maybe servers
GRANT EXECUTE ON FUNCTION public.compare_arrays(text[], text[]) TO users;
GRANT EXECUTE ON FUNCTION public.compare_arrays(text[], text[]) TO admins;
GRANT EXECUTE ON FUNCTION public.compare_arrays(text[], text[]) TO servers;

-- Very simple funtion to return arrays last element
-- Currently not used and will be removed in future
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

-- vhostdomaincat joins vhost and domain names
-- returns domain if vhost name is empty
-- returns vhost.domain if vhost is not empty
-- Created to help complexity of views.
-- Don't limit usage to vhosts, can be used also to other needs.
 
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

-- Similar to vhostdomaincat
-- returns name@domain
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

-- Find_domain function is used to find domain for vhost.
-- input text is full vhost name eg. myvhost.example.com
-- returns domains t_domains_id if domain found
-- else raises exception

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
      domainpart = regexp_replace(domain,'\*','\\*');
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
        m := regexp_replace(m,'\*','\\\\\*');
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

-- Get vhost name part from vhost string
-- eg. if vhosts domain is example.com and given text is
-- www.example.com function returns www
-- raises exception if domain for vhost is not found.

-- DROP FUNCTION IF EXISTS find_vhost(text);
CREATE OR REPLACE FUNCTION public.find_vhost(string text) RETURNS text AS $$
DECLARE
    vhost text;
    t text;
BEGIN
    IF string IS NULL OR string = '' THEN
      RAISE EXCEPTION 'No string given for function find_vhost';
      RETURN NULL;
    ELSE
        FOR vhost IN SELECT domains.name as name FROM domains
                    JOIN users USING(t_customers_id)
                    WHERE domains.t_domains_id = find_domain(string)
                    AND users.t_customers_id = domains.t_customers_id
                    AND (users.name = CURRENT_USER OR public.is_admin()) LIMIT 1
        LOOP
            t = regexp_replace(string, '\.?' || vhost || '$', '');
            RETURN t;
        END LOOP;
    END IF;
    RAISE EXCEPTION 'vhost for url % not found', string;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.find_vhost(text) TO users;
GRANT EXECUTE ON FUNCTION public.find_vhost(text) TO admins;

-- Some mail functions --

-- Like find_vhost
-- Returns part before @ on email address
-- raises exception if email address doesn't contain any @-marks
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


-- Find a domain from email address.
-- Like find_domain.
-- Trys to find a domain for an email address.
-- raises exception if email address is unvalid
-- or domain not found
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

-- array_accum aggrecate creates array from given element
-- element can be query retval or variable

CREATE AGGREGATE public.array_accum (anyelement)
(
    sfunc = array_append,
    stype = anyarray,
    initcond = '{}'
);

GRANT EXECUTE ON FUNCTION public.array_accum (anyelement) TO users;
GRANT EXECUTE ON FUNCTION public.array_accum (anyelement) TO admins;


-- unnest_multidim
-- Unnest multidimersional array by one level
-- returns set of arrays
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
-- returns port number
-- used on user_port_servers view
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
                    LEFT JOIN services.t_user_ports AS t_port ON ( t_user_ports.port + 1 ) = t_port.port
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
-- A little complex function to create s_tablename tables to store
-- table history.
-- creates table with columns on orginal table plus
-- old_xmin, old_xmax, s_tablename_id, operation, historized columns
-- history tables are used by renkisrv to track deleted and modifed rows
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

-- historize view function creates trigger to table
-- on update or delete to view, copy related tables rows to histrory tables
-- as if mailboxes view is changed, backup rows on t_mailboxes and t_mail_aliases tables
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
-- create_log_triggers function creates 
-- three triggers
-- insert, update and delete trigger
-- triggers uses historize_view trigger to insert rules to t_change_log
-- every t_* table should have those trigger
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
            EXECUTE PROCEDURE services.log_trigger($$' || pk::text || '$$)';
    EXECUTE 'DROP TRIGGER IF EXISTS ' || tablename::text || '_log_update ON ' || tablen::text;
    EXECUTE 'CREATE TRIGGER ' || tablename::text || '_log_update
            AFTER UPDATE ON ' || tablen::text || '
            FOR EACH ROW
            WHEN (OLD.* IS DISTINCT FROM NEW.*)
            EXECUTE PROCEDURE services.log_trigger($$' || pk::text || '$$)';
    EXECUTE 'DROP TRIGGER IF EXISTS ' || tablename::text || '_log_delete ON ' || tablen::text;
    EXECUTE 'CREATE TRIGGER ' || tablename::text || '_log_delete
            BEFORE DELETE ON ' || tablen::text || '
            FOR EACH ROW
            EXECUTE PROCEDURE services.log_trigger($$' || pk::text || '$$)';
END;
$f$ LANGUAGE plpgsql;

-- used by logger triggers to insert row to t_change_log
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
        EXECUTE 'INSERT INTO services.t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$, $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        EXECUTE 'SELECT ($1).' || TG_ARGV[0] || '::text' INTO t USING NEW;
        EXECUTE 'INSERT INTO services.t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$ , $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        EXECUTE 'SELECT ($1).' || TG_ARGV[0] || '::text' INTO t USING OLD;
        EXECUTE 'INSERT INTO services.t_change_log
                (table_ref, data_id, event_type, username)
                VALUES ($$' || TG_TABLE_NAME || '$$::regclass::oid, $$' || t || '$$, $$' || TG_OP || '$$, $$' || session_user || '$$)';
        RETURN OLD;
    END IF;
END;
$t$ LANGUAGE plpgsql
SECURITY DEFINER;


-- function tests if ip belong to subnet given by t_subnets_id
-- retruns true if match, else false
-- raises error, if t_subnets_id not found from t_subnets table
DROP FUNCTION IF EXISTS services.ip_on_subnet(inet, integer);
CREATE FUNCTION services.ip_on_subnet(ip inet, subnet_id integer)
RETURNS BOOLEAN
AS $f$
DECLARE
    isin boolean;
BEGIN
    isin := (t_subnets.address >> ip::inet) FROM services.t_subnets WHERE t_subnets.t_subnets_id = subnet_id;
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
                WHERE (users.name = CURRENT_USER::text OR public.is_admin())
                AND aliasname = ANY(customers.aliases)
        LOOP
        IF alias IS NOT NULL THEN
            RETURN TRUE;
        END IF;
    END LOOP;
    FOR alias IN SELECT customers.t_customers_id
                FROM users JOIN customers USING (t_customers_id)
                WHERE (users.name = CURRENT_USER::text OR public.is_admin())
                AND aliasname = users.name
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


-- Validate database name
-- permit only names matching either username, username_*, alias or alias_
-- TODO: don't work if you are admin and aim to add database to some other user
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

CREATE OR REPLACE FUNCTION add_vhost_dns_entries()
RETURNS TRIGGER
AS
$$
DECLARE
    ip4 text;
    ip6 text;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        ip4 := services.t_addresses.ip_address::text FROM services.t_services JOIN services.t_addresses USING (t_addresses_id) WHERE t_services.t_services_id = NEW.t_services_id;
        ip6 := services.t_addresses.ip6_address::text FROM services.t_services JOIN services.t_addresses USING (t_addresses_id) WHERE t_services.t_services_id = NEW.t_services_id;
        EXECUTE 'INSERT INTO services.t_dns_entries
        (type, key, value, t_domains_id)
        VALUES ($t$A$t$, $t$' || NEW.name || '$t$, $t$' || ip4 || '$t$,$t$' || NEW.t_domains_id || '$t$)';
        IF (ip6 IS NOT NULL) THEN
            EXECUTE 'INSERT INTO t_dns_entries
            (type, key, value, t_domains_id)
            VALUES ($t$AAAA$t$, $t$' || NEW.name || '$t$, $t$' || ip6 || '$t$,$t$' || NEW.t_domains_id || '$t$)';
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        ip4 := services.t_addresses.ip_address::text 
                FROM services.t_services 
                JOIN services.t_addresses USING (t_addresses_id) 
                WHERE t_services.t_services_id = NEW.t_services_id;
        ip6 := services.t_addresses.ip6_address::text
                FROM services.t_services
                JOIN services.t_addresses USING (t_addresses_id)
                WHERE services.t_services.t_services_id = NEW.t_services_id;
        EXECUTE 'DELETE FROM services.t_dns_entries
        WHERE t_domains_id = $t$' || OLD.t_domains_id || '$t$
        AND key = $t$' || OLD.name || '$t$
        AND ( TYPE = $t$A$t$ OR type = $t$AAAA$t$ )';
        EXECUTE 'INSERT INTO services.t_dns_entries
        (type, key, value, t_domains_id)
        VALUES ($t$A$t$, $t$' || NEW.name || '$t$, $t$' || ip4 || '$t$,$t$' || NEW.t_domains_id || '$t$)';
        IF (ip6 IS NOT NULL) THEN
            EXECUTE 'INSERT INTO t_dns_entries
            (type, key, value, t_domains_id)
            VALUES ($t$AAAA$t$, $t$' || NEW.name || '$t$, $t$' || ip6 || '$t$,$t$' || NEW.t_domains_id || '$t$)';
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        EXECUTE 'DELETE FROM services.t_dns_entries
        WHERE t_domains_id = $t$' || OLD.t_domains_id || '$t$
        AND key = $t$' || OLD.name || '$t$
        AND ( TYPE = $t$A$t$ OR type = $t$AAAA$t$ )';
        RETURN OLD;
    END IF;
END;
$$
LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION public.select_vhost_server(vhost text, services_id integer)
RETURNS INTEGER
AS
$$
DECLARE
    domain text;
    serv integer;
BEGIN
    domain := find_domain(vhost);
    IF (services_id IS NOT NULL) THEN
        FOR serv IN SELECT vhost_servers.t_services_id from vhost_servers WHERE t_services_id = services_id LOOP
            RETURN serv;
        END LOOP;
    END IF;
    IF (domain = 'kapsi.fi') THEN
        RETURN t_services_id FROM vhost_servers WHERE server = 'vhost-ssl.kapsi.fi';
    ELSE
        RETURN t_services_id FROM vhost_servers WHERE server = 'vhost.kapsi.fi';
    END IF;
END;
$$
language plpgsql;
