var _ = require('underscore');
var autoprefixer = require('autoprefixer');
var es = require('event-stream');
var gulp = require('gulp');
var livereload = require('gulp-livereload');
var ngAnnotate = require('gulp-ng-annotate');
var postcss = require('gulp-postcss');
var replace = require('gulp-replace');
var rjs = require('gulp-requirejs');
var sass = require('gulp-sass');
var spawnSync = require('child_process').spawnSync;
var uglify = require('gulp-uglify');
var plumber = require('gulp-plumber');
var fs = require('fs');
var version = require('gulp-version-number');
var cachebust = require('gulp-cache-bust');

var handleError = function (err) {
  console.log(err.name, ' in ', err.plugin, ': ', err.message);
  process.exit(1);
};

// Write version.js
gulp.task('write-version-js', function() {
  try {
    var data = spawnSync('git', ['rev-parse', '--short', 'HEAD']).output;
    var version = data.toString().split(',')[1].trim();
    var data2 = spawnSync('git', ['show', '-s', '--format=%ci', 'HEAD']).output;
    var date = data2.toString().split(' ')[0].split(',')[1].trim();
    var versionStr = version + " from " + date;
  }
  catch(err) {
    versionStr = 'Git version information not available';
  }
  fs.writeFileSync(
    'source/js/version.js',
    "define([], function () { return '" + versionStr + "'; });");
  console.log('Updated version.js to ' + versionStr);
});

// Copy assets, and vendor js files to the build directory
gulp.task('copy-assets-and-vendor-js', ['compile-sass'], function () {
  return es.concat(
    // update index.html to work when built
    gulp.src(['source/index.html'])
      .pipe(gulp.dest('build')),
    // copy config-require
    gulp.src(['source/js/config.js'])
      .pipe(uglify().on('error', handleError))
      .pipe(gulp.dest('build/js')),
    // copy template files
    gulp.src(['source/js/**/*.html'])
      .pipe(gulp.dest('build/js')),
    // copy vendor files
    gulp.src(['source/vendor/**/*'])
      .pipe(gulp.dest('build/vendor')),
    // copy assets
    gulp.src(['source/assets/**/*'])
      .pipe(gulp.dest('build/assets')),
    // minify requirejs
    gulp.src(['build/vendor/requirejs/require.js'])
      .pipe(uglify().on('error', handleError))
      .pipe(gulp.dest('build/vendor/requirejs')),
    // copy mpld3, instead of minifying because we're using constructor names for plugin identification
    gulp.src(['source/js/modules/charts/mpld3.v0.3.1.dev1.js'])
      .pipe(gulp.dest('build/js/modules/charts'))
  );
});

// Optimize the app into the build/js directory
gulp.task('compile-build-js-client-uglify', ['write-version-js'], function () {
  var configRequire = require('./source/js/config.js');
  var configBuild = {
    baseUrl: 'source',
    insertRequire: ['js/main'],
    name: 'js/main',
    out: 'main.js',
    optimize: 'none',
    wrap: true,
    excludeShallow: ['mpld3'] // excludes mpld3 from requirejs build
  };
  var config = _(configBuild).extend(configRequire);

  return rjs(config)
    .on('error', handleError)
    .pipe(ngAnnotate())
    .pipe(uglify().on('error', handleError)) // This is key -- it compresses the JS, but takes a long time
    .pipe(gulp.dest('build/js/'));
});

// Copy font-awesome files for icons
gulp.task('copy-font-awesome-icons', function() {
  return gulp.src('source/vendor/font-awesome/fonts/*')
    .pipe(gulp.dest('source/assets/fonts'))
});

// Process SASS to generate the CSS files
gulp.task('compile-sass', ['copy-font-awesome-icons'], function () {
  var cssGlobbing = require('gulp-css-globbing');
  var postcss = require('gulp-postcss');
  var sass = require('gulp-sass');

  return gulp.src(['source/sass/*.scss', '!source/sass/_*.scss'])
    .pipe(plumber(handleError))
    .pipe(cssGlobbing({
      extensions: '.scss'
    }))
    .pipe(sass())
    .pipe(postcss([
      require('postcss-assets')({
        basePath: 'source/',
        loadPaths: ['assets/fonts/', 'assets/images/']
      }),
      require('postcss-import')({
        path: 'source/'
      }),
      require('autoprefixer'),
      require('csswring')({
        preserveHacks: true,
        removeAllComments: true
      })
    ]))
    .pipe(gulp.dest('source/assets/css'));
});

// Watch
gulp.task('watch', [], function () {
  gulp.watch('source/sass/**/*.scss', ['sass']);
  gulp.watch('source/js/**/*.js', ['compile-build-js-client-uglify']);

  // enable livereload
  livereload.listen();

  gulp.watch([
      'source/assets/*.css',
      'source/index.html',
      'source/js/**/*'])
    .on(
      'change', livereload.changed);
});

// My (George's) first gulp task!
gulp.task('mytask', function () {
    gulp.src(['source/index.html'])
        .pipe(version({

            /**
             * Global version value
             * default: %MDS%
             */
            'value' : '%MDS%',

            /**
             * MODE: REPLACE
             * eg:
             *    'keyword'
             *    /regexp/ig
             *    ['keyword']
             *    [/regexp/ig, '%MD5%']]
             */
            'replaces' : [

                /**
                 * {String|Regexp} Replace Keyword/Rules to global value (config.value)
                 */
                '#{VERSION_REPlACE}#',

                /**
                 * {Array}
                 * Replace keyword to custom value
                 * if just have keyword, the value will use the global value (config.value).
                 */
                [/#{VERSION_REPlACE}#/g, '%TS%']
            ],


            /**
             * MODE: APPEND
             * Can coexist and replace, after execution to replace
             */
            'append' : {

                /**
                 * Parameter
                 */
                'key' : '_v',

                /**
                 * Whether to overwrite the existing parameters
                 * default: 0 (don't overwrite)
                 * If the parameter already exists, as a "custom", covering not executed.
                 * If you need to cover, please set to 1
                 */
                'cover' : 0,

                /**
                 * Appended to the position (specify type)
                 * {String|Array|Object}
                 * If you set to 'all', will apply to all type, rules will use the global setting.
                 * If an array or object, will use your custom rules.
                 * others will passing.
                 *
                 * eg:
                 *     'js'
                 *     ['js']
                 *     {type:'js'}
                 *     ['css', '%DATE%']
                 */
                'to' : [

                    /**
                     * {String} Specify type, the value is the global value
                     */
                    'css',

                    /**
                     * {Array}
                     * Specify type, keyword and cover rules will use the global
                     * setting, If you need more details, please use the object
                     * configure.
                     *
                     * argument 0 necessary, otherwise passing.
                     * argument 1 optional, the value will use the global value
                     */
                    ['image', '%TS%'],

                    /**
                     * {Object}
                     * Use detailed custom rules to replace, missing items will
                     * be taken in setting the global completion

                     * type is necessary, otherwise passing.
                     */
                    {
                        'type' : 'js',
                        'key' : '_v',
                        'value' : '%DATE%',
                        'cover' : 1
                    }
                ]
            },

            /**
             * Output to config file
             */
            'output' : {
                'file' : 'version.json'
            }
        }))
        .pipe(gulp.dest('mybuild/'))
    console.log('Ran gulp-version-number');
});

// My (George's) second gulp task
gulp.task('mytask2', function () {
    gulp.src(['source/index.html'])
        .pipe(cachebust({
            type: 'timestamp'
        }))
        .pipe(gulp.dest('mybuild/'))
    console.log('Ran gulp-cache-bust');
});

// Defaults -- WARNING, do version.js separately
gulp.task(
  'default',
  [
    'copy-assets-and-vendor-js',
    'compile-build-js-client-uglify',
  ]);

