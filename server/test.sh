#!/bin/bash

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

mkdir -p /tmp/uploads
cp ../optima/test.xlsx /tmp/uploads
mkdir -p static
cp ../optima/test.xlsx static
NOSE_NOCAPTURE=1 OPTIMA_TEST_CFG="${PWD}/test.cfg" nosetests $@
