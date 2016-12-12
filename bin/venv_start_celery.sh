#!/bin/bash

cd `dirname $0` # Make sure we're in the bin folder

./venv.sh

cd `dirname $0` # Make sure we're in the bin folder
cd ../server # Server folder

p-env/bin/celery -A server.webapp.tasks.celery_instance worker -l info
