#!/bin/bash

./sandbox.sh

p-env/bin/celery -A server.webapp.tasks.celery worker -l info
