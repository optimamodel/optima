ALTER TABLE working_projects ADD COLUMN parset_id uuid;
ALTER TABLE work_log ADD COLUMN parset_id uuid;
ALTER TABLE work_log ADD COLUMN result_id uuid;