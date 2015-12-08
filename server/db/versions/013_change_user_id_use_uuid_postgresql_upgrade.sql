ALTER TABLE users rename to users_old;
ALTER TABLE projects rename to projects_old;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users
(
  id uuid PRIMARY KEY default uuid_generate_v1mc(),
  old_id integer,
  name character varying(60),
  email character varying(200),
  password character varying(200),
  is_admin boolean DEFAULT false
);

CREATE TABLE projects (
    id uuid PRIMARY KEY default uuid_generate_v1mc(),
    name text,
    user_id uuid,
    datastart integer,
    dataend integer,
    populations json,
    created timestamp with time zone,
    updated timestamp with time zone,
    version text,
    settings bytea,
    data bytea
);

INSERT INTO users 
  (old_id, name, email, password, is_admin) 
  (select id, name, email, password, is_admin from users_old);

INSERT INTO projects
  (id, name, user_id, datastart, dataend, populations, created, updated, version, settings, data) 
  (SELECT a.id, a.name,b.id,a.datastart, a.dataend, a.populations, a.created, a.updated, a.version, a.settings, a.data FROM projects_old a, users b WHERE b.old_id = a.user_id);

ALTER TABLE users DROP COLUMN IF EXISTS old_id;

ALTER TABLE project_data DROP CONSTRAINT project_data_id_fkey;
ALTER TABLE working_projects DROP CONSTRAINT working_projects_id_fkey;
ALTER TABLE work_log DROP CONSTRAINT work_log_project_id_fkey;
ALTER TABLE parsets DROP CONSTRAINT parsets_project_id_fkey;
ALTER TABLE results DROP CONSTRAINT results_project_id_fkey;

DROP TABLE users_old;
DROP TABLE projects_old;

ALTER TABLE project_data
  ADD CONSTRAINT project_data_id_fkey FOREIGN KEY (id)
  REFERENCES projects (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE working_projects 
  ADD CONSTRAINT working_projects_id_fkey FOREIGN KEY (id)
  REFERENCES projects (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE work_log 
  ADD CONSTRAINT work_log_project_id_fkey FOREIGN KEY (project_id) 
  REFERENCES projects(id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE parsets 
  ADD CONSTRAINT parsets_project_id_fkey FOREIGN KEY (project_id) 
  REFERENCES projects(id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE results 
  ADD CONSTRAINT results_project_id_fkey FOREIGN KEY (project_id) 
  REFERENCES projects(id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;