#!/bin/bash

# Setup a virtualenv sandbox if not already
if [ ! -d "./p-env/" ]; then
  if [ "$1" == "--system" ]; then
    virtualenv --system-site-packages p-env
  else
    virtualenv p-env
  fi
fi

# Activate the virtualenv sandbox
source ./p-env/bin/activate

# Create a sorted list of existing dependencies
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

# Ensure that the optima modelling module is available from the sandbox
if [ ! -f "./p-env/lib/python2.7/site-packages/optima.egg-link" ]; then # not sure this is right
    echo "Installing optima in virtualenv for the celery webapps..."
    cd ..
    python setup.py develop
    cd server
fi

# delete to avoid some module import problems
if [ -f "../optima/optima.pyc" ]; then
  rm ../optima/*.pyc
fi

