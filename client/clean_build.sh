#!/bin/bash

if [ -d "node_modules" ]; then
  npm prune
fi

if [ -d "source/vendor" ]; then
  node_modules/bower/bin/bower prune
fi

# install npm and bower deps
npm install

# install ruby dependencies required to compile sass styles
bundle install

# build -> unit tests
node_modules/gulp/bin/gulp.js
