[Gulp](http://gulpjs.com/) flows
----------

Gulp tasks available:

* `gulp`
  Builds project into `build` directory.

* `gulp watch`
  Listens to changes to stylesheets and scripts and reloads browser page during development.

* `gulp karma-ci`
  Runs tests against the build (which should be run first) and quits, is good to use in CI scenarios.

* `gulp bump-version`
  Works with gitflow releases.

* `gulp karma`
  Starts Karma server watching scripts updates.

* `gulp sass`
  Compiles Sass project.

Tests
------

Tests use Jasmin for assertions.
You can write tests in both Coffee and JS
(see `/source/js/modules/home/home-ctrl.spec.js` and `/source/js/modules/home/home-ctrl.spec.coffee`).
