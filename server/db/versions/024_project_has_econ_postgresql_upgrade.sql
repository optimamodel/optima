ALTER TABLE projects DROP COLUMN IF EXISTS econ;
ALTER TABLE projects ADD COLUMN has_econ boolean;