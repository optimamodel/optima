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

CK: this stopped the server from running...
cd ..
python setup.py develop
cd server

migrate upgrade postgresql://optima:optima@localhost:5432/optima db/

TMP_DEPS=/tmp/temp_deps_${RANDOM}
pip freeze -l > ${TMP_DEPS}
if ! cmp ./requirements.txt ${TMP_DEPS} > /dev/null 2>&1
then
  echo "Installing Python dependencies ..."
  cat ${TMP_DEPS}
  pip install -r ./requirements.txt
fi

python api.py

