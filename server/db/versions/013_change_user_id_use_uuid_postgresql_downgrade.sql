ALTER TABLE projects
  DROP CONSTRAINT projects_user_id_fkey;

ALTER TABLE users rename to users_old;

CREATE TABLE users
(
  id serial PRIMARY KEY NOT NULL,
  old_id uuid,
  name character varying(60),
  email character varying(200),
  password character varying(200),
  is_admin boolean DEFAULT false
);

INSERT INTO users 
  (old_id, name, email, password, is_admin) 
  (select id, name, email, password, is_admin from users_old);

ALTER TABLE projects
  RENAME user_id TO old_user_id;
ALTER TABLE projects
  ADD user_id integer;

UPDATE projects
SET user_id=subquery.u_id
FROM (SELECT u.id as u_id, u.old_id as old_id
     FROM users AS u) AS subquery
WHERE old_user_id=subquery.old_id;

ALTER TABLE users DROP COLUMN IF EXISTS old_id;
ALTER TABLE projects DROP COLUMN IF EXISTS old_user_id;
ALTER TABLE projects ALTER COLUMN user_id SET NOT NULL;
  
DROP TABLE users_old;