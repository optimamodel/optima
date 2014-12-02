ALTER TABLE projects DROP COLUMN IF EXISTS creation_time;
ALTER TABLE projects DROP COLUMN IF EXISTS data_upload_time;
ALTER TABLE projects ALTER COLUMN model DROP DEFAULT;
ALTER TABLE projects ALTER COLUMN datastart TYPE varchar(20);
ALTER TABLE projects ALTER COLUMN dataend TYPE varchar(20);
ALTER TABLE projects ALTER COLUMN econ_datastart TYPE varchar(20);
ALTER TABLE projects ALTER COLUMN econ_dataend TYPE varchar(20);