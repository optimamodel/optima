ALTER TABLE projects ADD COLUMN working_model json;
ALTER TABLE projects ALTER COLUMN working_model SET DEFAULT '{}';