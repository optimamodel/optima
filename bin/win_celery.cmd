cd ..
python -m celery -A server.webapp.tasks.celery_instance worker -l info
cd bin