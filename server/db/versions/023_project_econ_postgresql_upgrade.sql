CREATE TABLE project_econ
(
  id uuid PRIMARY KEY,
  meta bytea,
  updated timestamp with time zone default now(),
  CONSTRAINT project_econ_id_fkey FOREIGN KEY (id)
      REFERENCES projects (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
ALTER TABLE projects ADD COLUMN econ bytea;