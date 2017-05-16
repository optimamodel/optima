# Linux workflow

The basic workflow consists of the following. Note that each of these should be executed (simultaneously is OK) in separate terminal windows.

0. `build_client.sh` -- rebuild the client, including SASS and JavaScript.
0. `start_server.sh` -- start the Flask/Twisted server, which serves the main Optima website.
0. `start_celery.sh` -- start the Celery task maanger, which handles asynchronous tasks like optimization.

# Windows workflow

As above, each of these should be executed in separate command windows from the `optima/bin` folder.

0. `win_build.cmd` -- equivalent to `build_client.sh`
0. `win_server.cmd` -- equivalent to `start_server.sh`
0. `win_celery.cmd` -- equivalent to `start_celery.sh`

# Mac workflow

0. `osx_boot.sh` -- performs all the above tasks

# Other files

0. `backup.py` -- unfinished script for backing up Optima projects/users.
0. `export.py` -- script for batch export of projects from database to files.
0. `import.py` -- script for batch import of projects from files to database.
0. `osx_check_postgres_redis.sh` -- helper script for `osx_boot.sh`, do not execute directly
0. `reset_db.py` -- script to reset/clear the Optima database if it gets bunged
0. `venv.sh` -- possibly deprecated equivalent of `start_server.sh` but making use of a virtual environment (instead of system Python)
0. `venv_start_celery.sh` -- as above, except for Celery
