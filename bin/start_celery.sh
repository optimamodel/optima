#!/bin/bash
# Run this second to start the Optima task manager.
# Assumes start_server.sh is already running.
# Version: 2016sep01

cd ..
python -m celery -A server.webapp.tasks.celery_instance worker -l info
