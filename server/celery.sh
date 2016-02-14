#!/bin/bash

if [ ! -d "./p-env/" ]; then
  if [ "$1" == "--system" ]; then
    virtualenv --system-site-packages p-env
  else
    virtualenv p-env
  fi
fi

source ./p-env/bin/activate

TMP_DEPS=/tmp/temp_deps_${RANDOM}

# create a sorted list of existing dependencies 
# against requirements.txt and compare that
# to a sorted version of requirements.txt
pip freeze -l > ${TMP_DEPS}
grep -f requirements.txt ${TMP_DEPS} > ${TMP_DEPS}.grep
sort ${TMP_DEPS}.grep > ${TMP_DEPS}.sort
sort ./requirements.txt > ${TMP_DEPS}.requirements.txt

if ! cmp ${TMP_DEPS}.requirements.txt ${TMP_DEPS}.sort > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./requirements.txt
fi

if [ ! -f "./p-env/lib/python2.7/site-packages/optima.egg-link" ]; then
    echo "Installing optima in virtualenv for the celery webapps..."
    cd ..
    python setup.py develop
    cd server
fi

p-env/bin/celery -A server.webapp.tasks.celery worker -l info
