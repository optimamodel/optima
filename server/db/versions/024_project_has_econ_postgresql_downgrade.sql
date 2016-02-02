ALTER TABLE projects ADD COLUMN econ bytea;
ALTER TABLE projects DROP COLUMN IF EXISTS has_econ;