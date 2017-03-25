#!/bin/bash
# Build the client.
# Usage:
#    ./build_client.sh # Build full client and minify JavaScript (slow)
#    ./build_client.sh quick # Build client but without minifying JavaScript

echo 'Building client...'

cd `dirname $0` # Make sure we're in this folder
cd ../client # Change to client folder

# Sometimes, old junk gets in the build
if [ -d "build" ]; then
  rm -r build
fi

if [ -d "node_modules" ]; then
  npm prune
fi

if [ -d "source/vendor" ]; then
  if [ -d "node_modules/bower/bin" ]; then
    node_modules/bower/bin/bower prune
  fi
fi

# install npm and bower deps
npm install --skip-installed

# compile sass scripts
if [ $# -eq 0 ]; then
	echo 'Compiling client (including minifying JavaScript)'
	node_modules/gulp/bin/gulp.js compile-build-js-client-uglify copy-assets-and-vendor-js write-version-js
else
	echo 'Compiling client (quick version)...'
	node_modules/gulp/bin/gulp.js compile-build-js-client-quick copy-assets-and-vendor-js write-version-js
fi