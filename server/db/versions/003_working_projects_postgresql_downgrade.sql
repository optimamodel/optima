ALTER TABLE working_projects RENAME COLUMN is_working to is_calibrating;
ALTER TABLE working_projects DROP COLUMN work_type;