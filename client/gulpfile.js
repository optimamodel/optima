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
var spawn = require('child_process').spawn;
var uglify = require('gulp-uglify');
var plumber = require('gulp-plumber');
var fs = require('fs');

var handleError = function (err) {
  console.log(err.name, ' in ', err.plugin, ': ', err.message);
  process.exit(1);
};

// Bump version
gulp.task('bump-version', function () {
  spawn('git', ['rev-parse', '--abbrev-ref', 'HEAD']).stdout.on('data', function (data) {

    // Get current branch name
    var branch = data.toString();

    // Verify we're on a release branch
    if (/^(release|hotfix)\/.*/.test(branch)) {
      var newVersion = branch.split('/')[1].trim();

      // Update client index.html
      gulp.src('./source/index.html')
        .pipe(replace(/(bust=v)(\d*\.?)*/g, '$1' + newVersion))
        .pipe(gulp.dest('./source'));

      var updateJson = function (file) {
        gulp.src(file)
          .pipe(replace(/("version" *: *")([^"]*)(",)/g, '$1' + newVersion + '$3'))
          .pipe(gulp.dest('./'));
      };

      updateJson('./bower.json');
      updateJson('./package.json');

      console.log('Successfully bumped to ' + newVersion);
    } else {
      console.error('This task should be executed on a release branch!');
    }

  });
});

// Write version.js
gulp.task('write-version-js', function() {
  spawn('git', ['rev-parse', '--short', 'HEAD']).stdout.on('data', function (data) {

    var version = data.toString().trim();

    spawn('git', ['show', '-s', '--format=%ci', 'HEAD']).stdout.on('data', function (data2) {

      var date = data2.toString().split(' ')[0].trim();

      var versionStr = version + " from " + date;
      fs.writeFileSync(
        'source/js/version.js',
        "define([], function () { return '" + versionStr + "'; });");

      console.log('Updated version.js to ' + versionStr);
    });

  });
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
    gulp.src(['source/js/modules/charts/mpld3.v0.3-patched.js'])
      .pipe(gulp.dest('build/js/modules/charts'))
  );
});

// Optimize the app into the build/js directory
gulp.task('compile-build-js-client', function () {
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
    .pipe(gulp.dest('build/js/'));

  // return rjs(config)
  //   .on('error', handleError)
  //   .pipe(ngAnnotate())
  //   .pipe(gulp.dest('build/js/'));

  // return gulp.src(['source/js/main.js'])
  //   .pipe(rjs(config).on('error', handleError))
  //   .pipe(ngAnnotate())
  //   .pipe(uglify().on('error', handleError))
  //   .pipe(gulp.dest('build/js/'));
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
gulp.task('watch', ['compile-sass'], function () {
  gulp.watch('source/sass/**/*.scss', ['sass']);

  // enable livereload
  livereload.listen();

  gulp.watch([
      'source/assets/*.css',
      'source/index.html',
      'source/js/**/*'])
    .on(
      'change', livereload.changed);
});

// Defaults
gulp.task(
  'default',
  [
    'compile-build-js-client',
    'copy-assets-and-vendor-js',
    'write-version-js'
  ]);

