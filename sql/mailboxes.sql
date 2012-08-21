
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

SELECT create_log_triggers('services.t_mail_aliases'::text);
SELECT create_log_triggers('services.t_mailboxes'::text);

DROP VIEW IF EXISTS public.mailboxes;
CREATE OR REPLACE VIEW public.mailboxes
AS
SELECT t_mailboxes.t_mailboxes_id, t_mailboxes.name || '@' || t_domain_mail.name as name, t_mailboxes.t_customers_id, t_mailboxes.created,
array_agg(t_mail_aliases.name || '@' || t_domains.name) AS aliases, t_domain_mail.t_domains_id
  FROM services.t_mailboxes
  JOIN services.t_customers USING (t_customers_id)
  JOIN services.t_users USING (t_customers_id)
  JOIN services.t_domains as t_domain_mail ON t_mailboxes.t_domains_id = t_domain_mail.t_domains_id
  LEFT JOIN services.t_mail_aliases USING (t_mailboxes_id)
  LEFT JOIN services.t_domains ON t_mail_aliases.t_domains_id = t_domains.t_domains_id
 WHERE (t_users.name = CURRENT_USER OR public.is_admin())
 GROUP BY t_mailboxes.t_mailboxes_id, t_domain_mail.t_domains_id, t_domain_mail.t_domains_id;

GRANT SELECT ON mailboxes TO users;
GRANT SELECT ON mailboxes TO admins;

CREATE OR REPLACE VIEW public.mail_aliases AS
SELECT t_mail_aliases.t_mail_aliases_id, t_mail_aliases.t_customers_id, t_mail_aliases.t_mailboxes_id,
emaildomaincat(t_mail_aliases.name, t_domains.name::text) AS alias,
t_domains.t_domains_id
FROM services.t_mail_aliases
JOIN services.t_domains on t_mail_aliases.t_domains_id = t_domains.t_domains_id
JOIN services.t_users ON t_mail_aliases.t_customers_id =  t_users.t_customers_id
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
FROM services.t_customers, users, services.t_domains
WHERE t_mailboxes.t_mailboxes_id = new.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_domains.t_customers_id = users.t_customers_id
AND t_customers.t_customers_id = users.t_customers_id
AND ((users.name = CURRENT_USER  AND NOT public.is_admin()) OR (public.is_admin() AND users.t_customers_id = OLD.t_customers_id));
-- delete removed alias row from t_vhost_aliases table
DELETE FROM services.t_mail_aliases
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
DELETE FROM services.t_mail_aliases USING services.t_customers, services.t_users
WHERE t_mail_aliases.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
-- LIMIT 50
;
DELETE FROM services.t_mailboxes USING services.t_customers, services.t_users
WHERE t_mailboxes.t_mailboxes_id = OLD.t_mailboxes_id
AND old.t_customers_id = t_customers.t_customers_id
AND t_customers.t_customers_id = t_users.t_customers_id
AND ( t_users.name = "current_user"()::text OR public.is_admin())
-- LIMIT 50
;
);

GRANT DELETE on mailboxes TO users;
GRANT DELETE on mailboxes TO admins;
