
# Optima 2.0 Front-End Client


## Notes

- bower to track client dependencies in vendor
- npm to track modules in `package.json` to be used in the gulp task runner
- written in Javascript 5
- angular 1.0 framework
    - angular url router -> uses `#` to simulate relative URL


## Scripts

- `clean_build.sh` installs dependencies then runs gulp to compile build and the run karam-ci unit-tests
- `clean_dev_build.sh` installs dependencies then compiles sass to CSS


## Gulp Task Runner

[Gulp](http://gulpjs.com/) tasks available:

- `gulp` builds project into `build` directory.
- `gulp watch` listens to changes to stylesheets and scripts and reloads browser page during development.
- `gulp bump-version` works with gitflow releases.
- `gulp compile-sass` compiles Sass project.
- `gulp compile-build-js-client` compiles a single-file version of client in `build`



