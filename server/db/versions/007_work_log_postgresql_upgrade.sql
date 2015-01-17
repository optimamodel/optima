CREATE TYPE work_status as ENUM('started', 'completed', 'cancelled', 'error');
CREATE TABLE work_log (
    id SERIAL PRIMARY KEY,
    work_type character varying(32),
    project_id integer,
    start_time timestamp with time zone DEFAULT now(),
    stop_time timestamp with time zone,
    status work_status,
    error text,
  CONSTRAINT work_log_project_id_fkey FOREIGN KEY (project_id) 
    REFERENCES projects(id) MATCH SIMPLE
    ON UPDATE NO ACTION ON DELETE NO ACTION
);
CREATE INDEX ix_work_log_project_id ON work_log USING btree (project_id);
ALTER TABLE working_projects ADD COLUMN work_log_id integer;
