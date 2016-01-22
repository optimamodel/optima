ALTER TABLE results DROP CONSTRAINT IF EXISTS results_parset_id_fkey;
ALTER TABLE results ADD CONSTRAINT results_parset_id_fkey FOREIGN KEY (parset_id) REFERENCES parsets(id);

