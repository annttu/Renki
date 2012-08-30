
-- Domains view contains only domains that user have
CREATE OR REPLACE VIEW public.dns_records
AS 
SELECT t_dns_records.t_dns_records_id,
t_dns_records.key,  t_dns_records.ttl, t_dns_records.type, t_dns_records.value,
domains.name as domain, t_dns_records.info, t_dns_records.manual
FROM t_dns_records
JOIN domains USING (t_domains_id);

CREATE OR REPLACE RULE dns_entries_insert
AS ON INSERT TO public.dns_records
DO INSTEAD
(
INSERT INTO services.t_dns_records (key, ttl, type, value, t_domains_id, info, manual)
SELECT NEW.key, NEW.ttl, NEW.type, NEW.value, domains.t_domains_id, NEW.info, TRUE
FROM domains
WHERE domains.name = NEW.domain
RETURNING t_dns_records.t_dns_records_id, t_dns_records.key, t_dns_records.ttl,
t_dns_records.type, t_dns_records.value,
(SELECT domains.name FROM domains WHERE domains.t_domains_id = t_dns_records.t_domains_id),
t_dns_records.info, t_dns_records.manual;
);

CREATE OR REPLACE RULE dns_records_delete
AS ON DELETE TO public.dns_records
DO INSTEAD
(
    DELETE FROM services.t_dns_records USING public.domains
    WHERE domains.name = OLD.domain
    AND OLD.manual = TRUE;
);

CREATE OR REPLACE RULE dns_records_update
AS ON UPDATE TO public.dns_records
DO INSTEAD
(
    UPDATE services.t_dns_records
    SET key = NEW.key, ttl = NEW.ttl, type = NEW.type, value = NEW.value,
    info = NEW.info
    FROM domains
    WHERE domains.name = OLD.domain
    AND t_dns_records.t_domains_id = domains.t_domains_id
    AND OLD.manual = TRUE;
);

GRANT SELECT,UPDATE,INSERT,DELETE ON public.dns_records TO users;
GRANT SELECT,UPDATE,INSERT,DELETE ON public.dns_records TO admins;

ALTER TABLE dns_records ALTER COLUMN ttl set DEFAULT 3600;

GRANT USAGE ON t_dns_records_t_dns_records_id_seq TO users;
GRANT USAGE ON t_dns_records_t_dns_records_id_seq TO admins;