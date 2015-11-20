ALTER TABLE projects rename to projects_old;
ALTER TABLE working_projects rename to working_projects_old;
ALTER TABLE work_log rename to work_log_old;
ALTER TABLE project_data rename to project_data_old;

ALTER TABLE projects_old DROP CONSTRAINT projects_user_id_fkey;
ALTER TABLE working_projects_old DROP CONSTRAINT working_projects_id_fkey;
ALTER TABLE work_log_old DROP CONSTRAINT work_log_project_id_fkey;
ALTER TABLE project_data_old DROP CONSTRAINT project_data_id_fkey;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE projects (
    id uuid PRIMARY KEY default uuid_generate_v1mc(),
    name text,
    user_id integer,
    datastart integer,
    dataend integer,
    populations json,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    version text,
    settings bytea,
    data bytea
);


CREATE TABLE project_data (
    id uuid PRIMARY KEY references projects(id),
    meta bytea,
    updated_at timestamp with time zone
);

CREATE TABLE working_projects (
    id uuid PRIMARY KEY references projects(id),
    is_working boolean,
    project bytea,
    work_type text,
    work_log_id uuid
);

CREATE TABLE work_log (
    id uuid PRIMARY KEY default uuid_generate_v1mc(),
    work_type text,
    project_id uuid references projects(id),
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    status work_status,
    error text
);

CREATE TABLE parsets (
  id uuid PRIMARY KEY default uuid_generate_v1mc(),
  project_id uuid references projects(id),
  name text,
  created_at timestamp with time zone,
  updated_at timestamp with time zone,
  pars bytea
);

CREATE TABLE results (
  id uuid PRIMARY KEY default uuid_generate_v1mc(),
  parset_id uuid references parsets(id),
  project_id uuid references projects(id),
  calculation_type text,
  blob bytea
);



