#!/bin/bash
# Build the client.
#
# Usage is complicated:
#    ./build_client.sh # Build full client and minify JavaScript
#
# Version: 2017jun03

echo 'Building client...'

cd `dirname $0` # Make sure we're in this folder
cd ../client # Change to client folder

# Sometimes, old junk gets in the build
if [ -d "build" ]; then
  echo -e '\nRemoving existing build directory...'
  rm -r build
fi

if [ -d "node_modules" ]; then
  echo -e '\nPruning node modules...'
  npm prune
fi

if [ -d "source/vendor" ]; then
  if [ -d "node_modules/bower/bin" ]; then
  	echo -e '\nPruning bower modules...'
    node_modules/bower/bin/bower prune
  fi
fi

# install npm and bower deps
echo -e '\nInstalling npm dependencies...'
npm install --skip-installed

# compile sass scripts and minify javascript and copy client and everything
echo -e '\nCompiling client (including minifying JavaScript)...'
node_modules/gulp/bin/gulp.js

# This needs to be done separately, until the compile-build-js-client-uglify task 
# is made to terminate correctly in gulpfile.js.
echo -e '\nAdding cache-busting strings...'
gulp cache-bust

echo -e '\nDone.'