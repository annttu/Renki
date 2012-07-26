-- Create user groups

CREATE GROUP users;
CREATE GROUP admins;
CREATE GROUP servers;

-- grant some permissions
GRANT CONNECT ON DATABASE services to admins;
GRANT CONNECT ON DATABASE services to servers;

-- create schema
CREATE SCHEMA services;

-- alter search path to find also tables on services schema
alter database services SET search_path TO public,services;


-- CREATE TYPES --

CREATE TYPE t_change_log_event_type AS ENUM ('INSERT', 'UPDATE', 'DELETE');
CREATE type domain_type AS enum ('MASTER', 'SLAVE', 'NONE');
CREATE TYPE event_type AS ENUM ('INSERT','UPDATE', 'DELETE');
CREATE TYPE t_hosts_type AS ENUM ('HARDWARE', 'VIRTUAL');

-----------------------
-- CREATE SOME USERS --
-----------------------

-- normal user
CREATE USER username NOCREATEDB NOINHERIT IN GROUP users;

-- admin
CREATE USER admin NOCREATEDB NOINHERIT IN GROUP admins;
GRANT USAGE ON SCHEMA services TO admin;