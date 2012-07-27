
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

SELECT create_log_triggers('services.t_subnets'::text);

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

SELECT services.create_log_triggers('t_hosts'::text);

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

SELECT create_log_triggers('services.t_addresses'::text);
