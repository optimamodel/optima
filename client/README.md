
# Optima 2.0 Front-End Client


## Notes

- bower to track client dependencies in vendor
- npm to track devDependencies
- nginx to serve the client to the browser
- p.conf.js - protractor - is this used?
- written in Javascript 5
- angular single-page-app -> uses `#` to simulate URL directory system


## Scripts

- `clean_build.sh` installs dependencies then runs gulp to compile build and the run karam-ci unit-tests
- `clean_dev_build.sh` installs dependencies then compiles sass to CSS


## Gulp Task Runner

[Gulp](http://gulpjs.com/) tasks available:

- `gulp` builds project into `build` directory.
- `gulp watch` listens to changes to stylesheets and scripts and reloads browser page during development.
- `gulp karma-ci` runs tests against the build (which should be run first) and quits, is good to use in CI scenarios.
- `gulp bump-version` works with gitflow releases.
- `gulp karma` starts Karma server watching scripts updates.
- `gulp sass` compiles Sass project.


## Tests

- karma to run tests includes tests-main.js etc.
- karma-ci to run tests on compiled build
- Tests use Jasmin for assertions.
- You can write tests in both Coffee and JS
  (see `/source/js/modules/home/home-ctrl.spec.js`
   and `/source/js/modules/home/home-ctrl.spec.coffee`).


