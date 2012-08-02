
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
    document_root text,
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
    CONSTRAINT valid_name CHECK (name ~* '^[a-z0-9\.\-\^*]*$'),
    CONSTRAINT valid_document_root CHECK (document_root IS NULL OR document_root ~* '^\/[a-z0-9\.\/\-\^*]+$' )
);

ALTER TABLE services.t_vhosts add unique(t_domains_id, name);

SELECT create_log_triggers('services.t_vhosts'::text);

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
