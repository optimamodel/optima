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
var regexreplace = require('gulp-regex-replace');

var handleError = function (err) {
  console.log(err.name, ' in ', err.plugin, ': ', err.message);
  process.exit(1);
};

// Write version.js with the git version and date info
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
    gulp.src(['source/js/modules/charts/mpld3.v0.4.12.js'])
      .pipe(gulp.dest('build/js/modules/charts'))
  );
});

// Optimize the app into the build/js directory
// NOTE: Something is not completed correctly here because the console never registers
// a Finished for this task (which will cause any gulp tasks with dependencies on
// 'compile-build-js-client-uglify' to also not complete. Possible reason: if any
// @import dependencies in the sass fail, this will silently fail (argh!).
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

// Task for doing cache-busting on the build files.
// Note, there should be a ['compile-build-js-client-uglify'] set here as a dependency, but
// this does not terminate correctly, so I can't use it.
// So, currently a separate gulp call (gulp cache-bust)
// needs to be made after the main call by the building scripts.
gulp.task('cache-bust', function () {
    // Grab the current date, returning 'unknown' if this doesn't work.
    try {
    	var today = new Date();
		var version = today.getFullYear()+'.'+(today.getMonth()+1)+'.'+today.getDate()+'_'+today.getHours()+'.'+today.getMinutes()+'.'+today.getSeconds();
    }
    catch(err) {
        version = 'unknown';
    }
    return es.concat(
        // Do a regular expression replace "cacheBust=xxx" -> "cacheBust=_version_" for just index.html.
        gulp.src(['build/index.html'])
            .pipe(regexreplace({
                regex: 'cacheBust=xxx',
                replace: ('cacheBust=' + version)
            }))
            .pipe(gulp.dest('build/')),
        // Do a regular expression replace "cacheBust=xxx" -> "cacheBust=_version_" for js files in modules.
        gulp.src(['build/js/**/*.html', 'build/js/**/*.js'])
            .pipe(regexreplace({
                regex: 'cacheBust=xxx',
                replace: ('cacheBust=' + version)
            }))
            .pipe(gulp.dest('build/js/'))
    )
});

// Defaults
gulp.task(
  'default',
  [
    'copy-assets-and-vendor-js',
    'compile-build-js-client-uglify',
    //'cache-bust'  // uncomment once we can figure out how to fix 'compile-build-js-client-uglify' to halt correctly
  ]
);

