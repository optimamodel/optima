
# Optima 2.0 webclient

- the Optima webclient is a single-page-application written in 
  Javascript ES5, using the Angular 1.0 framework.
- the entry point of the developing version of the webclient is `source/index.html`. 
- **WARNING**, many of these notes are outdated!

## Building the Webclient

First off, here is the script to build the webclient:

- `../bin/build_client.sh` for production in the `build` folder
- `../bin/build_client.sh quick` for a quick local build (no minification)

In these scripts:
 
- `npm` is used to install all the `node` modules
required to compile the assets required for the webserver.  
- `gulpfile.js` describes all the steps required to build the
  webclient, and the compilation is carried out by `gulp`, a node-based
  task-runner (batch commands, compilation, copying etc.)
- `package.json` lists all the npm modules to download, including
  `gulp` and all the modules that the `gulpfile` requires
- `bower` is used to load modules required in the webclient itself
  and the modules are stored in the `source/vendor` folder
- `bower.json` lists all the third-party modules required
  within the webclient
- there is a hook in `package.json` that runs `bower` to install
  the third-party libraries in `source/vendor`
- the CSS files are written as `sass` files in the `source/sass`
  directory, and are compiled by `gulp-sass`, and
  ultimately placed in the `*__``*source/assets/css` folder

## Compiling the webclient

The compilation of the webclient is carried out by [Gulp](http://gulpjs.com/) and is 
described in `gulpfile.js`. The different tasks that can be carried out are:
 
- `gulp` builds client into `build` directory.
- `gulp watch` listens to changes to stylesheets and scripts and reloads browser page during development.
- `gulp bump-version` updates JSON files and `source/index.html` with tagged releases.
- `gulp write-version-js` updates `source/js/version.js` to the latest git version and date
- `gulp compile-sass` compiles the SASS files in `source/sass` to CSS files in `source/assets/css`.
- `gulp compile-build-js-client` compiles a single-file version of the webclient in `build`

## Layout of the webclient

- uses the AMD method for loading modules
- uses `angular.bootstrap` for modal dialogs
- uses `toastr` for the notifications
- uses `mpld3` and `d3` to display the graphs exported from matplotlib
- uses `angularjs-slider` for sliders
- uses `font-awesome` for web-icons
- `normalize.css` is used for cross-browser compatibility
- the `sass` files follow the [MCSS](http://operatino.github.io/MCSS/en/) convention
- uses `angular-tooltip` - https://github.com/samiralajmovic/tooltip
- uses `angular-loading-bar` - http://chieffancypants.github.io/angular-loading-bar/

In the `source` folder:

- the `source/assets` folder holds CSS files, images and icons
- the `source/vendor` folder stores third-party libraries used in the webclient such as angular
- the `source/index.html` is the entry-point into the webclient
- the `source/js` holds the javascript files and internal modules
- the `source/sass` holds the SASS files that will be compiled into CSS files

In the `source/js` folder:

- `version.js` lists the current git branch and commit date, to be displayed in the help page
- `config.js` is the loading point of all modules, vendor and internal
- `main.js` the main loading point, with pre-loading hooks
- `app.js` the entry point of the Angular app where all modules are loaded
- the `modules` folder:
    - `admin` handles administrator user and projects views
    - `analysis` scenario and optimization pages
    - `chart` directives, services and libraries to render graphs
    - `common` utility functions and directives
    - `contact` feedback/contact page
    - `help` help page, loads `version.js`
    - `model` the calibration page
    - `portfolio` the geospatial analysis
    - `program` program set and cost functions page
    - `project` project management (home), project edit/populations, and population modal dialog, and some services
    - `sha224` stripped down SHA224 module to hash passwords
    - `ui` menu items and common modal dialogs
    - `user` user manager and user-api services, login, register, and user-edit pages
- services and directives
    - `active-project` stores/extracts active project from local storage
    - `project-api-service` sores/extracts projects from webserver
    - `resources-user` sores/extracts users from webserver
    - `user-manager` stores/extracts current user






