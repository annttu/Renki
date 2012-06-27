
CREATE GROUP users;
CREATE GROUP admins;
GRANT CONNECT ON DATABASE services to admins;

CREATE SCHEMA services;
alter database services SET search_path TO public,services;

CREATE OR REPLACE FUNCTION public.is_admin() RETURNS bool AS $$
DECLARE
    adm bool;
BEGIN
    FOR adm IN SELECT true
                FROM pg_roles
                JOIN pg_group ON pg_roles.oid IN (SELECT unnest(grolist))
                WHERE groname = 'admins' AND pg_roles.rolname = CURRENT_USER LIMIT 1
        LOOP
            RETURN adm;
        END LOOP;
    RETURN false;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.is_admin() TO users;
GRANT EXECUTE ON FUNCTION public.is_admin() TO admins;

-- Function for array comparsions

CREATE OR REPLACE FUNCTION compare_arrays(first text[], second text[])
    RETURNS SETOF text
    AS $$
DECLARE
    retval text;
BEGIN
    FOR retval IN SELECT a.a FROM (SELECT unnest(first::text[]) as a) as a
               LEFT JOIN (select a from unnest(second::text[]) as a) as b using(a) WHERE b.a is null LOOP
               RETURN NEXT retval;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.last_elem (text[]) RETURNS text AS $$
 SELECT $1[array_length($1,1)];
$$ LANGUAGE SQL;

GRANT EXECUTE ON FUNCTION public.last_elem(text[]) TO users;


-- array reverse function ( currently not used )

CREATE OR REPLACE FUNCTION array_reverse(anyarray) RETURNS anyarray AS $$
SELECT ARRAY(
    SELECT $1[i]
    FROM generate_subscripts($1,1) AS s(i)
    ORDER BY i DESC
);
$$ LANGUAGE 'sql' STRICT IMMUTABLE;

CREATE OR REPLACE FUNCTION vhostdomaincat(vhost text, domain text) RETURNS text AS $$
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

CREATE OR REPLACE FUNCTION emaildomaincat(name text, domain text) RETURNS text AS $$
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

-- epic funtion to find domain for vhost

-- DROP FUNCTION IF EXISTS find_domain(text);
CREATE OR REPLACE FUNCTION public.find_domain(domain text) RETURNS integer AS $$
    DECLARE
        partarray text[];
        domainpart text;
        r RECORD;
        m text;

    BEGIN
    IF domain IS NULL OR domain = '' THEN
      RETURN -1;
    ELSE
      domainpart = domain;
      partarray = regexp_split_to_array(domain, '\.');
      FOREACH m IN ARRAY partarray
      LOOP
        FOR r IN SELECT domains.t_domains_id as id
        FROM domains
        JOIN users USING (t_customers_id)
        WHERE ( users.name = CURRENT_USER OR public.is_admin() )
        AND domains.name =  domainpart
        AND (SELECT COUNT(*)
            FROM domains
            WHERE ( users.name = CURRENT_USER OR public.is_admin() )
            AND domains.name = domainpart
        ) = 1
        LOOP
            RETURN r.id;
        END LOOP;
        domainpart = regexp_replace(domainpart, '^' || m || '\.', '');

    END LOOP;
    END IF;
    RAISE EXCEPTION 'Domain for vhost % not found', domain;
    RETURN NULL;
  END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION public.find_domain(text) TO users;


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


-- Some mail functions --


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

-- multi dimersional array

CREATE OR REPLACE FUNCTION array_agg2(text, text) RETURNS text[]
AS 'select ARRAY[$1::text, $2::text];'
LANGUAGE SQL
IMMUTABLE
RETURNS NULL ON NULL INPUT;

/*
DROP AGGREGATE IF EXISTS array_agg2(text,text);
CREATE AGGREGATE array_agg2(text, text)
(
    sfunc = array_accum,
    stype = text[],
    initcond = '{}'
);
*/

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


CREATE AGGREGATE array_accum (anyelement)
(
    sfunc = array_append,
    stype = anyarray,
    initcond = '{}'
);

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



CREATE OR REPLACE FUNCTION public.find_free_port(hosts_id integer) 
RETURNS integer 
AS $$
DECLARE
    port integer;
    host_id integer;
    lower_limit integer = 40000;
    upper_limit integer = 65536;
BEGIN
    FOR host_id IN SELECT t_hosts.t_hosts_id FROM services.t_hosts 
                   WHERE hosts_id = t_hosts.t_hosts_id
                   AND allow_users_add_ports = true LIMIT 1
        LOOP
        FOR port IN SELECT (t_user_ports.port + 1) AS port 
                    FROM services.t_user_ports 
                    LEFT JOIN t_user_ports AS t_port ON ( t_user_ports.port + 1 ) = t_port.port 
                    WHERE t_port.port IS NULL AND t_user_ports.t_hosts_id = host_id LIMIT 1
            LOOP
                IF port > lower_limit AND port < upper_limit THEN
                    RETURN port;
                END IF;
            END LOOP;
        FOR port IN SELECT (MAX(t_user_ports.port) + 1) as max_port FROM services.t_user_ports WHERE t_user_ports.t_hosts_id = host_id 
                    AND (SELECT (MAX(t_user_ports.port) + 1) FROM services.t_user_ports WHERE t_user_ports.t_hosts_id = 1) > lower_limit
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



--
-- Functios end
--



CREATE TYPE t_change_log_event_type AS ENUM ('INSERT', 'UPDATE', 'DELETE');

CREATE TABLE t_change_log
( t_change_log_id serial NOT NULL PRIMARY KEY,
  created timestamptz DEFAULT NOW(),
  table_ref oid NOT NULL,
  event_type t_change_log_event_type NOT NULL,
  data_id integer NOT NULL,
  transaction_id bigint NOT NULL DEFAULT txid_current()
);

COMMENT ON COLUMN t_change_log.event_type IS 'insert,update, delete';


-- CUSTOMERS
-- You maybe want to user somekind of wrapper for this, but this is default way to do this.

CREATE TABLE t_customers (
    t_customers_id integer NOT NULL,
    name text NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    closed timestamp with time zone
);

CREATE OR REPLACE RULE users_change_log_insert
AS ON INSERT TO t_customers
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_customers'::regclass::oid, currval('services.t_customers_t_customers_id_seq'), 'INSERT');

CREATE OR REPLACE RULE domains_change_log_update
AS ON UPDATE TO t_customers
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_customers'::regclass::oid, old.t_customers_id, 'UPDATE');

CREATE OR REPLACE RULE domains_change_log_delete
AS ON DELETE TO t_customers
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_customers'::regclass::oid, old.t_customers_id, 'DELETE');

-- USERS

CREATE TABLE t_users (
    t_users_id integer NOT NULL,
    t_customers_id integer NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    name text NOT NULL,
    lastname text,
    firstnames text,
    phone text,
    password_changed timestamp with time zone DEFAULT now() NOT NULL
);

CREATE OR REPLACE RULE users_change_log_insert
AS ON INSERT TO t_users
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_users'::regclass::oid, NEW.t_users_id, 'INSERT');
-- VALUES ('t_users'::regclass::oid, currval('services.t_users_t_users_id_seq'), 'INSERT');

CREATE OR REPLACE RULE domains_change_log_update
AS ON UPDATE TO t_users
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_users'::regclass::oid, old.t_users_id, 'UPDATE');

CREATE OR REPLACE RULE domains_change_log_delete
AS ON DELETE TO t_users
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_users'::regclass::oid, old.t_users_id, 'DELETE');

CREATE OR REPLACE VIEW users AS
    SELECT t_users.t_customers_id, t_users.name, t_users.lastname, t_users.firstnames, t_users.phone
    FROM services.t_users
    WHERE (t_users.name = ("current_user"())::text OR public.is_admin());

-- DOMAINS


CREATE type domain_type AS enum ('master', 'slave', 'none');

CREATE TABLE t_domains (
    t_domains_id serial NOT NULL PRIMARY KEY,
    name text UNIQUE NOT NULL,
    shared boolean DEFAULT false NOT NULL,
    t_customers_id integer,
    dns boolean DEFAULT true NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    updated timestamp with time zone,
    refresh_time integer DEFAULT 28800 NOT NULL,
    retry_time integer DEFAULT 7200 NOT NULL,
    expire_time integer DEFAULT 1209600 NOT NULL,
    minimum_cache_time integer DEFAULT 21600 NOT NULL,
    ttl integer DEFAULT 10800 NOT NULL,
    admin_address text DEFAULT 'hostmaster@kapsi.fi'::text NOT NULL,
    domain_type domain_type DEFAULT 'master'::domain_type NOT NULL,
    masters inet[],
    allow_transfer inet[]
);

CREATE OR REPLACE RULE domains_change_log_insert
AS ON INSERT TO t_domains
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_domains'::regclass::oid, currval('services.t_domains_t_domains_id_seq'), 'INSERT');

CREATE OR REPLACE RULE domains_change_log_update
AS ON UPDATE TO t_domains
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_domains'::regclass::oid, old.t_domains_id, 'UPDATE');

CREATE OR REPLACE RULE domains_change_log_delete
AS ON DELETE TO t_domains
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_domains'::regclass::oid, old.t_domains_id, 'DELETE');

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




CREATE OR REPLACE RULE t_dns_keys_change_log_insert
AS ON INSERT TO t_dns_keys
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_dns_keys'::regclass::oid, currval('services.t_dns_keys_t_dns_keys_id_seq'), 'INSERT');

CREATE OR REPLACE RULE domains_change_log_update
AS ON UPDATE TO t_dns_keys
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_dns_keys'::regclass::oid, old.t_dns_keys_id, 'UPDATE');

CREATE OR REPLACE RULE domains_change_log_delete
AS ON DELETE TO t_dns_keys
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_dns_keys'::regclass::oid, old.t_dns_keys_id, 'DELETE');



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
WHERE ( t_users.name = "current_user"()::text OR public.is_admin());

CREATE OR REPLACE RULE domains_insert
AS ON INSERT TO public.domains
DO INSTEAD
INSERT INTO t_domains
(t_customers_id, name, shared,dns,refresh_time,retry_time,expire_time,minimum_cache_time,ttl,admin_address,domain_type,masters,allow_transfer)
SELECT t_customers_id,
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
AND (( t_users.name = CURRENT_USER AND NOT public.is_admin()) OR public.is_admin())
LIMIT 50;

ALTER TABLE public.domains ALTER shared SET DEFAULT false;
ALTER TABLE public.domains ALTER dns SET DEFAULT true;
ALTER TABLE public.domains ALTER refresh_time SET DEFAULT 28800;
ALTER TABLE public.domains ALTER retry_time SET DEFAULT 7200;
ALTER TABLE public.domains ALTER minimum_cache_time SET DEFAULT 21600;
ALTER TABLE public.domains ALTER expire_time SET DEFAULT 1209600;
ALTER TABLE public.domains ALTER ttl SET DEFAULT 10800;
ALTER TABLE public.domains ALTER domain_type SET DEFAULT 'master';
ALTER TABLE public.domains ALTER admin_address SET DEFAULT 'hostmaster@kapsi.fi';


------------
-- VHOSTS --
------------

CREATE TABLE t_vhosts (
    t_vhosts_id integer NOT NULL,
    t_customers_id integer NOT NULL,
    log_access boolean DEFAULT false NOT NULL,
    www_servers_id integer,
    created timestamp with time zone DEFAULT now(),
    redirect_to text,
    CONSTRAINT valid_redirect CHECK (((redirect_to IS NULL) OR (redirect_to ~* '^https?://'::text)))
);

ALTER TABLE ONLY t_vhosts
    ADD CONSTRAINT t_vhosts_pkey PRIMARY KEY (t_vhosts_id);

ALTER TABLE t_vhosts
    ADD constraint valid_redirect CHECK ( redirect_to is null OR redirect_to ~* '^https?://' );

CREATE OR REPLACE RULE vhosts_change_log_insert
AS ON INSERT TO t_vhosts
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhosts'::regclass::oid, currval('services.t_vhosts_t_vhosts_id_seq'), 'INSERT');

CREATE OR REPLACE RULE vhosts_change_log_update
AS ON UPDATE TO t_vhosts
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhosts'::regclass::oid, old.t_vhosts_id, 'UPDATE');

CREATE OR REPLACE RULE vhosts_change_log_delete
AS ON DELETE TO t_vhosts
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhosts'::regclass::oid, old.t_vhosts_id, 'DELETE');

CREATE OR REPLACE VIEW public.vhosts
AS
SELECT t_vhosts.t_vhosts_id, t_vhosts.t_customers_id, t_vhosts.created,
-- array_agg(t_vhost_aliases.name) AS aliases,
-- I found this to compicated for my skills
-- array_agg_custom(array_agg2(t_vhost_aliases.name::text, t_vhost_aliases.t_domains_id::text)) as aliases,
array_agg(vhostdomaincat(t_vhost_aliases.name::text,t_domains.name::text)::text) as aliases,
redirect_to
FROM t_vhosts
JOIN t_customers USING (t_customers_id)
JOIN t_users USING (t_customers_id)
LEFT JOIN t_vhost_aliases USING (t_vhosts_id)
LEFT JOIN t_domains ON t_domains.t_domains_id = t_vhost_aliases.t_domains_id
WHERE (t_users.name = CURRENT_USER OR public.is_admin())
GROUP BY t_vhosts.t_vhosts_id;

ALTER TABLE vhosts ALTER created SET DEFAULT NOW();
ALTER TABLE vhosts ALTER redirect_to SET DEFAULT NULL;

GRANT SELECT,INSERT,UPDATE,DELETE ON vhosts TO users;

CREATE OR REPLACE RULE vhosts_insert
AS ON INSERT TO public.vhosts
DO INSTEAD
(
SELECT nextval('services.t_vhosts_t_vhosts_id_seq'::regclass);
INSERT INTO t_vhosts
(t_customers_id, redirect_to, t_vhosts_id)
SELECT users.t_customers_id,
NEW.redirect_to,
currval('services.t_vhosts_t_vhosts_id_seq'::regclass)
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = NEW.t_customers_id))
-- Limit vhost count to something sane
AND (SELECT COUNT(vhosts.t_vhosts_id) FROM vhosts, users  WHERE users.name = CURRENT_USER AND vhosts.t_customers_id = users.t_customers_id) < 50
-- don't insert without aliases
AND array_upper(new.aliases, 1) is not null
RETURNING t_vhosts_id, t_customers_id, created, ARRAY[]::text[], redirect_to;
-- add aliases also
INSERT INTO t_vhost_aliases (t_customers_id, t_domains_id, name, t_vhosts_id)
SELECT users.t_customers_id, 
find_domain(unnest(new.aliases)) as domain, 
find_vhost(unnest(new.aliases)) as name, 
currval('services.t_vhosts_t_vhosts_id_seq'::regclass)
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = NEW.t_customers_id));
);

-- Check that all foreign keys match to user

CREATE OR REPLACE RULE vhosts_update
AS ON UPDATE TO vhosts
DO INSTEAD
( UPDATE t_vhosts
SET
redirect_to = NEW.redirect_to
FROM t_customers, users
WHERE t_vhosts.t_vhosts_id = new.t_vhosts_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id));
-- delete removed alias row from t_vhost_aliases table
DELETE FROM t_vhost_aliases
WHERE t_vhosts_id = old.t_vhosts_id AND
t_vhost_aliases_id IN (
    SELECT vhost_aliases.t_vhost_aliases_id
    FROM vhost_aliases
    WHERE vhost_aliases.alias IN (
        SELECT compare_arrays(old.aliases::text[], new.aliases::text[])
    )
);
INSERT INTO t_vhost_aliases (t_customers_id, t_vhosts_id, name, t_domains_id)
SELECT users.t_customers_id,  old.t_vhosts_id,
find_vhost(compare_arrays(new.aliases::text[], old.aliases::text[])) as name,
find_domain(compare_arrays(new.aliases::text[], old.aliases::text[])) as t_domains_id
FROM users
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id))
);

CREATE OR REPLACE RULE vhosts_delete
AS ON DELETE TO vhosts
DO INSTEAD
(
DELETE FROM t_vhost_aliases USING t_customers, t_users
WHERE t_vhost_aliases.t_vhosts_id = OLD.t_vhosts_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (t_users.name = CURRENT_USER  OR public.is_admin())
LIMIT 50;
DELETE FROM t_vhosts USING t_customers, t_users
WHERE t_vhosts.t_vhosts_id = OLD.t_vhosts_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND (t_users.name = CURRENT_USER OR public.is_admin())
LIMIT 50;
);


-- Aliases change log
CREATE OR REPLACE RULE vhost_aliases_change_log_insert
AS ON INSERT TO t_vhost_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_aliases'::regclass::oid, currval('services.t_vhost_aliases_t_vhost_aliases_id_seq'), 'INSERT');

CREATE OR REPLACE RULE vhost_alias_change_log_update
AS ON UPDATE TO t_vhost_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_aliases'::regclass::oid, old.t_vhost_aliases_id, 'UPDATE');

CREATE OR REPLACE RULE vhost_alias_change_log_delete
AS ON DELETE TO t_vhost_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_aliases'::regclass::oid, old.t_vhost_aliases_id, 'DELETE');


/*
-- redirects change log
CREATE OR REPLACE RULE t_vhost_redirects_change_log_insert
AS ON INSERT TO t_vhost_redirects
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_redirects'::regclass::oid, currval('services.t_mail_aliases_t_mail_aliases_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_vhost_redirects_change_log_update
AS ON UPDATE TO t_vhost_redirects
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_redirects'::regclass::oid, new.t_vhost_redirects_id, 'UPDATE');

CREATE OR REPLACE RULE t_vhost_redirects_change_log_delete
AS ON DELETE TO t_vhost_redirects
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vhost_redirects'::regclass::oid, old.t_vhost_redirects_id, 'DELETE');
*/


CREATE OR REPLACE VIEW public.vhost_aliases AS
SELECT t_vhost_aliases_id, vhostdomaincat(t_vhost_aliases.name, t_domains.name::text) as alias
FROM t_vhost_aliases
JOIN t_domains USING (t_domains_id)
JOIN t_customers ON t_vhost_aliases.t_customers_id =  t_customers.t_customers_id
JOIN t_users ON t_vhost_aliases.t_customers_id =  t_users.t_customers_id
WHERE (t_users.name = CURRENT_USER  OR public.is_admin());

GRANT SELECT ON public.vhost_aliases TO users;

-- ------------
-- Mailboxes --
-- ------------

CREATE OR REPLACE RULE t_mail_aliases_change_log_insert
AS ON INSERT TO t_mail_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mail_aliases'::regclass::oid, currval('services.t_mail_aliases_t_mail_aliases_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_mail_aliases_change_log_update
AS ON UPDATE TO t_mail_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mail_aliases'::regclass::oid, old.t_mail_aliases_id, 'UPDATE');

CREATE OR REPLACE RULE t_mail_aliases_change_log_delete
AS ON DELETE TO t_mail_aliases
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mail_aliases'::regclass::oid, old.t_mail_aliases_id, 'DELETE');

CREATE OR REPLACE RULE t_mailboxes_change_log_insert
AS ON INSERT TO t_mailboxes
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mailboxes'::regclass::oid, currval('services.t_mailboxes_t_mailboxes_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_mailboxes_change_log_update
AS ON UPDATE TO t_mailboxes
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mailboxes'::regclass::oid, new.t_mailboxes_id, 'UPDATE');

CREATE OR REPLACE RULE t_mailboxes_change_log_delete
AS ON DELETE TO t_mailboxes
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_mailboxes'::regclass::oid, old.t_mailboxes_id, 'DELETE');

ALTER TABLE t_mailboxes ADD UNIQUE(t_domains_id,name);

DROP VIEW public.mailboxes;
CREATE OR REPLACE VIEW public.mailboxes
AS
SELECT t_mailboxes.t_mailboxes_id, t_mailboxes.name || '@' || t_domains_mail.name as name, t_mailboxes.t_customers_id, t_mailboxes.created,
array_agg(t_mail_aliases.name || '@' || t_domains.name) AS aliases
  FROM t_mailboxes
  JOIN t_customers USING (t_customers_id)
  JOIN t_users USING (t_customers_id)
  JOIN t_domains as t_domains_mail USING (t_domains_id)
  LEFT JOIN t_mail_aliases USING (t_mailboxes_id)
  LEFT JOIN t_domains ON t_mail_aliases.t_domains_id = t_domains.t_domains_id
 WHERE (t_users.name = CURRENT_USER OR public.is_admin())
 GROUP BY t_mailboxes.t_mailboxes_id, t_domains_mail.t_domains_id;

GRANT SELECT ON mailboxes TO users;

CREATE OR REPLACE VIEW public.mail_aliases AS
SELECT t_mail_aliases_id, emaildomaincat(t_mail_aliases.name, t_domains.name::text) AS alias
FROM t_mail_aliases
JOIN t_domains on t_mail_aliases.t_domains_id = t_domains.t_domains_id
JOIN t_users ON t_mail_aliases.t_customers_id =  t_users.t_customers_id
WHERE (t_users.name = CURRENT_USER OR public.is_admin());

GRANT SELECT ON public.mail_aliases TO users;


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
RETURNING t_mailboxes_id as t_mailboxes_id, name as name, t_customers_id as t_customers_id, created as created, ARRAY[]::text[] as aliases;
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
GRANT USAGE ON t_mailboxes_t_mailboxes_id_seq to users;
GRANT USAGE ON t_change_log_t_change_log_id_seq to users;
GRANT USAGE ON t_mail_aliases_t_mail_aliases_id_seq TO users;


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

CREATE OR REPLACE RULE mailboxes_delete
AS ON DELETE TO mailboxes
DO INSTEAD
(
DELETE FROM t_mail_aliases USING t_customers, t_users
WHERE t_mail_aliases.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
LIMIT 50;
DELETE FROM t_mailboxes USING t_customers, t_users
WHERE t_mailboxes.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
LIMIT 50;
);

GRANT DELETE ON mailboxes TO users;

----------------------------------
-- vlans_id | tag | name | info --
----------------------------------

CREATE TABLE services.t_vlans
(t_vlans_id serial PRIMARY KEY NOT NULL,
tag integer NOT NULL,
name text NOT NULL,
info text);

ALTER TABLE t_vlans ADD CONSTRAINT "vlans_id_check" CHECK (tag > 0 AND tag < 65536);

CREATE OR REPLACE RULE t_vlans_change_log_insert
AS ON INSERT TO t_vlans
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vlans'::regclass::oid, currval('services.t_vlans_t_vlans_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_vlans_change_log_update
AS ON UPDATE TO t_vlans
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vlans'::regclass::oid, old.t_vlans_id, 'UPDATE');

CREATE OR REPLACE RULE t_vlans_change_log_delete
AS ON DELETE TO t_vlans
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_vlans'::regclass::oid, old.t_vlans_id, 'DELETE');

-------------
-- subnets --
-------------

CREATE TABLE services.t_subnets
(   t_subnets_id serial NOT NULL PRIMARY KEY,
    name text NOT NULL,
    location text NOT NULL,
    info text,
    t_vlans_id integer references t_vlans,
    address inet NOT NULL
);

CREATE OR REPLACE RULE t_subnets_change_log_insert
AS ON INSERT TO t_subnets
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_subnets'::regclass::oid, currval('services.t_subnets_t_subnets_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_subnets_change_log_update
AS ON UPDATE TO t_subnets
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_subnets'::regclass::oid, old.t_subnets_id, 'UPDATE');

CREATE OR REPLACE RULE t_subnets_change_log_delete
AS ON DELETE TO t_subnets
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_subnets'::regclass::oid, old.t_subnets_id, 'DELETE');


------------------------------
-- Hosts aka. computers etc --
------------------------------


CREATE TYPE t_hosts_type AS ENUM ('HARDWARE', 'VIRTUAL');

CREATE TABLE services.t_hosts
(
    t_hosts_id serial NOT NULL PRIMARY KEY,
    name text NOT NULL UNIQUE,
    type t_hosts_type NOT NULL DEFAULT 'VIRTUAL',
    t_domains_id integer references t_domains,
    t_customers_id integer references t_customers,
    allow_users_add_ports boolean NOT NULL DEFAULT false,
    -- services maybe many to many relation to t_services table
    -- not implemented yet
);

ALTER TABLE services.t_hosts ADD CONSTRAINT valid_name CHECK (name ~* '^[a-z0-9]+$');
ALTER TABLE services.t_hosts ADD UNIQUE (name, t_domains_id);

CREATE OR REPLACE RULE t_hosts_change_log_insert
AS ON INSERT TO t_hosts
DO ALSO
INSERT INTO services.t_change_log
(table_ref, data_id, event_type)
VALUES ('t_hosts'::regclass::oid, currval('services.t_ip_addresses_t_ip_addresses_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_hosts_change_log_update
AS ON UPDATE TO t_hosts
DO ALSO
INSERT INTO services.t_change_log
(table_ref, data_id, event_type)
VALUES ('t_hosts'::regclass::oid, old.t_hosts_id, 'UPDATE');

CREATE OR REPLACE RULE t_hosts_change_log_delete
AS ON DELETE TO services.t_hosts
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_hosts'::regclass::oid, old.t_hosts_id, 'DELETE');



------------------
-- IP-addresses --
------------------

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

CREATE OR REPLACE RULE t_ip_addresses_change_log_insert
AS ON INSERT TO services.t_ip_addresses
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_ip_addresses'::regclass::oid, currval('services.t_ip_addresses_t_ip_addresses_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_ip_addresses_change_log_update
AS ON UPDATE TO services.t_ip_addresses
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_ip_addresses'::regclass::oid, old.t_ip_addresses_id, 'UPDATE');

CREATE OR REPLACE RULE t_ip_addresses_change_log_delete
AS ON DELETE TO services.t_ip_addresses
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_ip_addresses'::regclass::oid, old.t_ip_addresses_id, 'DELETE');

----------------
-- User ports --
----------------

-- ports are hosts functionality
-- ports are for users on shell servers

CREATE TABLE services.t_user_ports
(
    t_user_ports_id serial PRIMARY KEY NOT NULL,
    t_customers_id integer references t_customers NOT NULL,
    port integer NOT NULL,
    info text,
    t_hosts_id integer references t_hosts NOT NULL,
    approved boolean NOT NULL DEFAULT false,
    active boolean NOT NULL DEFAULT true
);

ALTER TABLE t_user_ports ADD CONSTRAINT valid_port CHECK ((port > 1024 AND port <= 30000 ) OR ( port >= 40000 AND port < 65536));
ALTER TABLE t_user_ports ADD UNIQUE (port, t_hosts_id);

CREATE OR REPLACE RULE t_user_ports_change_log_insert
AS ON INSERT TO t_user_ports
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_user_ports'::regclass::oid, currval('services.t_user_ports_t_user_ports_id_seq'), 'INSERT');

CREATE OR REPLACE RULE t_user_ports_change_log_update
AS ON UPDATE TO t_user_ports
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_user_ports'::regclass::oid, old.t_user_ports_id, 'UPDATE');

CREATE OR REPLACE RULE t_user_ports_change_log_delete
AS ON DELETE TO t_user_ports
DO ALSO
INSERT INTO t_change_log
(table_ref, data_id, event_type)
VALUES ('t_user_ports'::regclass::oid, old.t_user_ports_id, 'DELETE');

CREATE OR REPLACE VIEW public.hosts
AS 
SELECT 
t_hosts.t_hosts_id as hosts_id, 
public.find_free_port(t_hosts.t_hosts_id) as port, 
t_hosts.name || '.' || t_domains.name as host
FROM t_hosts
JOIN t_domains USING (t_domains_id)
JOIN t_users ON t_users.name = CURRENT_USER
WHERE t_hosts.allow_users_add_ports = true
AND t_domains.t_domains_id = t_hosts.t_domains_id;

GRANT SELECT ON hosts TO users;

CREATE OR REPLACE VIEW public.user_ports
AS 
SELECT 
t_user_ports.t_user_ports_id,
t_user_ports.t_customers_id,
port,
t_hosts.name || '.' || t_domains.name as host,
t_user_ports.info as info,
t_user_ports.approved,
t_user_ports.active
FROM t_user_ports
JOIN t_customers USING (t_customers_id)
JOIN t_users USING (t_customers_id)
JOIN t_hosts USING (t_hosts_id)
JOIN t_domains ON t_hosts.t_domains_id = t_domains.t_domains_id
WHERE ( t_users.name = CURRENT_USER OR public.is_admin())
AND t_domains.t_domains_id = t_hosts.t_domains_id
AND t_user_ports.t_hosts_id = t_hosts.t_hosts_id; 

ALTER TABLE public.user_ports ALTER active SET DEFAULT true;
 
GRANT SELECT ON public.user_ports TO users;

CREATE OR REPLACE RULE user_ports_insert
AS ON INSERT
TO public.user_ports
DO INSTEAD 
INSERT INTO t_user_ports
(t_customers_id, port, t_hosts_id, info, approved, active)
SELECT users.t_customers_id, hosts.port, hosts.hosts_id, NEW.info,
    (SELECT COUNT(user_ports.t_user_ports_id) 
     FROM user_ports, users  
     WHERE users.name = CURRENT_USER 
     AND user_ports.t_customers_id = users.t_customers_id) < 5,
new.active
FROM hosts
JOIN users ON (users.name = CURRENT_USER)
WHERE ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = NEW.t_customers_id))
AND (SELECT COUNT(user_ports.t_user_ports_id) FROM user_ports, users  WHERE users.name = CURRENT_USER AND user_ports.t_customers_id = users.t_customers_id) < 20
AND hosts.host = NEW.host
RETURNING t_user_ports_id,t_customers_id,port, info, (SELECT hosts.host FROM hosts WHERE hosts.hosts_id = t_hosts_id ),approved,active;

GRANT INSERT ON user_ports TO users;

CREATE OR REPLACE RULE user_ports_update
AS ON UPDATE
TO public.user_ports
DO INSTEAD 
(
UPDATE t_user_ports SET
active = NEW.active,
info = NEW.info
FROM t_customers, users
WHERE t_user_ports.t_user_ports_id = new.t_user_ports_id
AND t_user_ports.t_customers_id = users.t_customers_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id));
);

GRANT UPDATE ON user_ports TO users;

CREATE OR REPLACE RULE user_ports_delete
AS ON DELETE
TO public.user_ports
DO INSTEAD
(
DELETE FROM t_user_ports USING t_customers, t_users
WHERE t_user_ports.t_user_ports_id = OLD.t_user_ports_id 
AND t_user_ports.t_customers_id = t_customers.t_customers_id
AND t_users.t_customers_id = t_customers.t_customers_id 
AND (t_users.name = CURRENT_USER OR public.is_admin())
);

GRANT DELETE ON user_ports TO users;

-----------------------
-- CREATE SOME USERS --
-----------------------

-- normal user
CREATE USER username NOCREATEDB NOINHERIT IN GROUP users;

-- admin
CREATE USER admin NOCREATEDB NOINHERIT IN GROUP admins;
GRANT USAGE ON SCHEMA services TO admin;