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

source ./p-env/bin/activate

migrate upgrade postgresql://optima:optima@localhost:5432/optima db/

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

python api.py

