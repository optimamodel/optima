dropdb optima
createdb optima
cd ..
python -c "import server.api; server.api.init_db()"
