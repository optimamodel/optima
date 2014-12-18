ALTER TABLE projects ADD COLUMN model json;
ALTER TABLE projects ALTER COLUMN model SET DEFAULT '{}';