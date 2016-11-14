
# Optima 2.0 Front-End Client


## Notes

- npm to track modules in 
    - `package.json` to be used in the `gulpfile.js` task runner
    - npm will run bower at postinstall
- bower to install client dependencies  
    - from `bower.json` 
    - to `source/vendor` directory as listed in `.bowerrc`
- written in Javascript 5
- angular 1.0 framework
    - angular url router - uses `#` to simulate relative URL


## Scripts

- `clean_build.sh` installs dependencies then runs gulp to compile production build in `build` 
- `clean_dev_build.sh` installs dependencies, compiles sass to CSS, gets version in `source`


## Gulp Task Runner

[Gulp](http://gulpjs.com/) tasks available:

- `gulp` builds client into `build` directory.
- `gulp watch` listens to changes to stylesheets and scripts and reloads browser page during development.
- `gulp bump-version` works with gitflow releases.
- `gulp compile-sass` compiles Sass project.
- `gulp compile-build-js-client` compiles a single-file version of client in `build`



