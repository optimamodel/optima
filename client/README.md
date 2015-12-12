Optima - Frontend
=================

This has been made  using seed project [ng-seed](https://github.com/StarterSquad/ngseed/wiki)

Installation
------------

    # Run script ./clean_build.sh.

      In case you face issue in executing ./clean_build.sh you can alternatively execute commands:
       1. npm install
       2. npm -g install bower (if you do not have bower already globally installed)
       3. npm -g install gulp (if you do not have gulp already globally installed)
       4. Create file client/js/version.js and add this content to it "define([], function () { return 'last_commit_short_hash'; });"
          (Where last_commit_short_hash is short hash for the past commit).


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
  Works with gitglow releases.

* `gulp karma`
  Starts Karma server watching scripts updates.

* `gulp sass`
  Compiles Sass project.

## Tests

Tests use Jasmin for assertions.
You can write tests in both Coffee and JS
(see `/source/js/modules/home/home-ctrl.spec.js` and `/source/js/modules/home/home-ctrl.spec.coffee`).


User login
-------------

In order to use the application you need to login a registered user. In order to register a new user visit the endpoint:
`http://optima.dev/#/register` and you'll be able to add yours
