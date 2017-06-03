cd ..\client
rmdir build /s /q
node node_modules\gulp\bin\gulp.js
:: remove line below once we've fixed gulpfile.js correctly
:: we need to fix the termination of compile-build-js-client-uglify task
gulp cache-bust  
cd ..\bin