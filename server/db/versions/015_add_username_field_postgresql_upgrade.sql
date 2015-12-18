ALTER TABLE users ADD COLUMN username varchar(255);
UPDATE users SET username=email;
