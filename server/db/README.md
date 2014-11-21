This is a database migration repository.

More information at
http://code.google.com/p/sqlalchemy-migrate/


Setup Migrations
------------

Database migrations are setup to be done automatically during deploy. To run them yourself, do the following:

    pip install sqlalchemy-migrate

    cd <your-git-root>/Optima/

    migrate version_control postgresql://optima:optima@localhost:5432/optima server/db/

this initiates the migration in your local DB.


Create Migration Script
------------

When you want to create new migration script, do:

    migrate sql_script postgresql://optima:optima@localhost:5432/optima <migration_name> server/db/

This will create two empty files with names like 00X_<migration_name>_(down|up)grade.sql. These are upgrade and downgrade migration, correspondingly. Edit them accordingly.


Run Migrations
------------

To run the migration, do:

    migrate upgrade postgresql://optima:optima@localhost:5432/optima server/db/

To undo the migration, do:

    # Usage: migrate downgrade URL REPOSITORY_PATH VERSION
    migrate downgrade postgresql://optima:optima@localhost:5432/optima server/db/ 0
