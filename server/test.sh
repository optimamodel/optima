#!/bin/bash

PGPASSWORD=test psql -h 127.0.0.1 -d optima_test -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' -U test

if [ ! -d "./p-env/" ]; then
  if [ "$1" == "--system" ]; then
    virtualenv --system-site-packages p-env
    shift
  else
    virtualenv p-env
  fi
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

mkdir -p /tmp/uploads
cp ../optima/test.xlsx /tmp/uploads
mkdir -p static
cp ../optima/test.xlsx static
NOSE_NOCAPTURE=1 OPTIMA_TEST_CFG="${PWD}/test.cfg" nosetests $@
