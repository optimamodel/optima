# Probably need `sudo su postgres` for first two commands
pkill postgres
pkill python
dropdb optima
createdb optima
python reset_db.py

