#!/bin/bash

./env.sh

p-env/bin/celery -A server.webapp.tasks.celery_instance worker -l info
