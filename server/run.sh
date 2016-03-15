#!/bin/bash

if [ ! -d "./p-env/" ]; then
  if [ "$1" == "--system" ]; then
    virtualenv --system-site-packages p-env
  else
    virtualenv p-env
  fi
fi

if [ ! -f "config.py" ]; then
  cp config.example.py config.py
fi

# delete to avoid some module import problems
if [ -f "../optima/optima.pyc" ]; then
  rm ../optima/optima.pyc
fi

source ./p-env/bin/activate

migrate upgrade postgresql://optima:optima@localhost:5432/optima db/

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

python api.py

