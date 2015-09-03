#!/bin/bash

if [ -d "node_modules" ]; then
  npm prune
fi

if [ -d "source/vendor" ]; then
  if [ -d "node_modules/bower/bin" ]; then
    node_modules/bower/bin/bower prune
  fi
fi

# install npm and bower deps
npm install

# add version file
commit=$(git rev-parse --verify --short HEAD)
tee source/js/version.js <<< "define([], function () { return '$commit'; });"

# compile sass scripts
node_modules/gulp/bin/gulp.js sass
