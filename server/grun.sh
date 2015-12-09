#!/bin/bash

if [ ! -f "src/config.py" ]; then
  cp config.example.py config.py
fi

if [ ! -d "./p-env/" ]; then
    virtualenv p-env
fi

source ./p-env/bin/activate

TMP_DEPS=/tmp/temp_deps_${RANDOM}
pip freeze -l > ${TMP_DEPS}
if ! cmp ./requirements.txt ${TMP_DEPS} > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./requirements.txt
fi
pip install gunicorn

gunicorn --workers 2 --error-logfile=- --log-file=- --bind 127.0.0.1:5000 --log-level debug api:app