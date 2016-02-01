#!/bin/bash

if [ ! -d "./server/p-env/" ]; then
  if [ "$1" == "--system" ]; then
    virtualenv --system-site-packages server/p-env
  else
    virtualenv server/p-env
  fi
fi

source ./server/p-env/bin/activate

TMP_DEPS=/tmp/temp_deps_${RANDOM}
pip freeze -l > ${TMP_DEPS}
if ! cmp ./server/requirements.txt ${TMP_DEPS} > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./server/requirements.txt
fi

server/p-env/bin/celery -A server.webapp.tasks.celery worker -l info
