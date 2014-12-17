ALTER TABLE working_projects RENAME COLUMN is_calibrating to is_working;
ALTER TABLE working_projects ADD COLUMN work_type varchar(32);