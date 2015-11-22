ALTER TABLE projects rename to new_projects;
ALTER TABLE project_data rename to new_project_data;
ALTER TABLE working_projects rename to new_working_projects;
ALTER TABLE work_log rename to new_work_log;

ALTER TABLE projects_old rename to projects;
ALTER TABLE working_projects_old rename to working_projects;
ALTER TABLE work_log_old rename to work_log;
ALTER TABLE project_data_old rename to project_data;

DROP TABLE new_working_projects;
DROP TABLE new_work_log;
DROP TABLE new_project_data;
DROP TABLE results;
DROP TABLE parsets;
DROP TABLE new_projects;

ALTER TABLE projects ADD CONSTRAINT projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE working_projects ADD CONSTRAINT working_projects_id_fkey FOREIGN KEY (id) REFERENCES projects(id);
ALTER TABLE project_data ADD CONSTRAINT project_data_id_fkey FOREIGN KEY (id) REFERENCES projects(id);
ALTER TABLE work_log ADD CONSTRAINT work_log_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id);
