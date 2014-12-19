CREATE TABLE project_data
(
  id integer NOT NULL,
  meta bytea,
  CONSTRAINT project_data_pkey PRIMARY KEY (id),
  CONSTRAINT project_data_id_fkey FOREIGN KEY (id)
      REFERENCES projects (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);

