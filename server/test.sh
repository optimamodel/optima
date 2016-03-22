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

if [ ! -f "./p-env/lib/python2.7/site-packages/optima.egg-link" ]; then
    echo "Installing optima in virtualenv for the server..."
    cd ..
    python setup.py develop
    cd server
fi

# create a sorted list of existing dependencies
# against requirements.txt and compare that
# to a sorted version of requirements.txt
TMP_DEPS=/tmp/temp_deps_${RANDOM}
pip freeze -l | grep -f requirements.txt | sort > ${TMP_DEPS}
sort ./requirements.txt > ${TMP_DEPS}.requirements.txt
if ! cmp ${TMP_DEPS}.requirements.txt ${TMP_DEPS} > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./requirements.txt
fi

mkdir -p /tmp/uploads
cp ../tests/simple.xlsx /tmp/uploads/test.xlsx
mkdir -p static
cp ../tests/simple.xlsx static/test.xlsx

OPTIMA_TEST_CFG="${PWD}/test.cfg" nosetests -c nose.cfg $@

rm -rf static
