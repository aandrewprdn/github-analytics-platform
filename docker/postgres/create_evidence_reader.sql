-- Read-only role for Evidence dashboards. Idempotent: safe to re-run.
-- Run as the database owner (the role dbt uses), via:  make evidence-setup
-- psql variables: dbname, reader_user, reader_password, marts_schema
\set ON_ERROR_STOP on

-- Create the role once, then (re)set its password so it always matches .env
SELECT format('CREATE ROLE %I LOGIN', :'reader_user')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'reader_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'reader_user', :'reader_password') \gexec

GRANT CONNECT ON DATABASE :"dbname" TO :"reader_user";

-- Dashboards may only read the tested, deduplicated marts — not raw/staging or Airflow tables
CREATE SCHEMA IF NOT EXISTS :"marts_schema";
GRANT USAGE ON SCHEMA :"marts_schema" TO :"reader_user";
GRANT SELECT ON ALL TABLES IN SCHEMA :"marts_schema" TO :"reader_user";

-- dbt drops and recreates mart tables on every run; default privileges make the new
-- tables readable too (they apply to tables created by the role running this script)
ALTER DEFAULT PRIVILEGES IN SCHEMA :"marts_schema" GRANT SELECT ON TABLES TO :"reader_user";
