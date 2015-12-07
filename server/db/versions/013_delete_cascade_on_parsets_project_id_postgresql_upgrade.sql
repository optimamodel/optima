ALTER TABLE parsets
DROP CONSTRAINT parsets_project_id_fkey,
ADD CONSTRAINT parsets_project_id_fkey
   FOREIGN KEY (project_id)
   REFERENCES projects(id)
   ON DELETE CASCADE;

ALTER TABLE results
DROP CONSTRAINT results_project_id_fkey,
ADD CONSTRAINT results_project_id_fkey
   FOREIGN KEY (project_id)
   REFERENCES projects(id)
   ON DELETE CASCADE;

ALTER TABLE results
DROP CONSTRAINT results_parset_id_fkey,
ADD CONSTRAINT results_parset_id_fkey
   FOREIGN KEY (parset_id)
   REFERENCES parsets(id)
   ON DELETE CASCADE;
