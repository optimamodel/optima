#!/bin/bash
# Setup a virtualenv environment for the server 

cd `dirname $0`/../server # Make sure we're in the server folder

echo $(pwd)
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
# against venvrequirements.txt and compare that
# to a sorted version of venvrequirements.txt
TMP_DEPS=/tmp/temp_deps_${RANDOM}
pip freeze -l | grep -f venvrequirements.txt | sort > ${TMP_DEPS}
sort ./venvrequirements.txt > ${TMP_DEPS}.venvrequirements.txt
if ! cmp ${TMP_DEPS}.venvrequirements.txt ${TMP_DEPS} > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./venvrequirements.txt
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

