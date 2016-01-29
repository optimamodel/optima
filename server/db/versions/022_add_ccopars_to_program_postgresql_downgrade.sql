ALTER TABLE programs DROP COLUMN IF EXISTS ccopars;
ALTER TABLE programs ADD COLUMN blob bytea;
