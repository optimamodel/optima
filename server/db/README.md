Setup migrations
------------

More information at
http://code.google.com/p/sqlalchemy-migrate/

Database migrations are setup to be done automatically during deploy. To run them yourself, do the following:

    pip install sqlalchemy-migrate psycopg2

    cd <your-git-root>/Optima/

    migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/

this initiates the migration in your local DB.

Create migration script
------------

When you want to create new migration script, do:

    migrate script_sql postgresql <migration_name> server/db/

This will create two empty files with names like 00X_<migration_name>\_(down|up)grade.sql. These are upgrade and downgrade migration, correspondingly. Edit them accordingly.


Run migrations
------------

To run the migration, do:

    migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/

To undo the migration, do:

    # Usage: migrate downgrade URL REPOSITORY_PATH VERSION
    migrate downgrade postgresql://optima:optima@localhost:5432/optima server/db/ 0

CAVEAT. If you applied the previous migrations manually, you have to update the migrate_version table:

    update migrate_version set version=<previous version>;

I.e. if you want to apply migration 3 and your database already has all previous migrations, verify that migrate_version.version=2 before running migrations.


Drop and re-create your database
--------------------------------

/!\ If you do this, you will loose the full content of the database

First exit any database shell (e.g. `psql`) that might be running, and stop the Flask server. Then, from the repository's root directory, run the following commands:

    dropdb optima
    createdb optima -O optima
    source server/p-env/bin/activate
    migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/
    migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/
