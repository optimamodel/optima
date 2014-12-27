DROP TABLE project_data;
ALTER TABLE projects ADD COLUMN data_upload_time timestamp with time zone;
ALTER TABLE projects ALTER COLUMN data_upload_time set default now();
