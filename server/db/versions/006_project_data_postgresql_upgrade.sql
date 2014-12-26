CREATE TABLE project_data
(
  id SERIAL PRIMARY KEY,
  meta bytea,
  upload_time timestamp with time zone,
  CONSTRAINT project_data_id_fkey FOREIGN KEY (id)
      REFERENCES projects (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
ALTER TABLE project_data ALTER COLUMN upload_time set default now();
ALTER TABLE projects DROP COLUMN IF EXISTS data_upload_time;