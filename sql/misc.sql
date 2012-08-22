
-- For better performance

CREATE INDEX ON t_domains (t_domains_id);
CREATE INDEX ON t_domains (t_customers_id);
CREATE INDEX ON t_domains (name);
CREATE INDEX ON t_users (t_customers_id);
CREATE INDEX ON t_users (t_users_id);
CREATE INDEX ON t_vhosts_id (t_vhosts_id);
CREATE INDEX ON t_vhosts (t_vhosts_id);
CREATE INDEX ON t_vhosts (t_domains_id);
CREATE INDEX ON t_vhosts (t_customers_id);
CREATE INDEX ON t_vhosts (t_users_id);

CREATE INDEX ON t_aliases (t_customers_id);
CREATE INDEX ON t_aliases (alias);