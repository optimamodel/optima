#!/bin/bash
# Run this second to start the Optima task manager.
# Assumes start_server.sh is already running.
# Version: 2016sep01

tput reset # Try to reset the screen, but don't worry if it fails
cd `dirname $0` # Make sure we're in the bin folder
cd .. # Main Optima folder
python -m celery -A server.webapp.tasks.celery_instance worker -l info
