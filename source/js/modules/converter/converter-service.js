define([
  'angular'
], function (angular) {
  'use strict';

  return angular.module('app.converter', [])

    .service('converter', [function () {
      var service = {
        json2cvs: function (input) {
          var array = typeof input != 'object' ? JSON.parse(input) : input;

          var str = '';

          for (var i = 0; i < array.length; i++) {
            var line = '';

            for (var index in array[i]) {
              line += array[i][index] + ',';
            }

            // Here is an example where you would wrap the values in double quotes
            // for (var index in array[i]) {
            //    line += '"' + array[i][index] + '",';
            // }

            line.slice(0, line.Length - 1);

            str += line + '\r\n';
          }

          var result = new String(str);

          result.download = function () {
            download(str, 'Export to CVS', 'text/cvs');
          };

          return result;
        }
      };

      /**
       * Helpers
       */

      function download(content, filename, contentType) {
        if (!contentType) {
          contentType = 'application/octet-stream';
        }

        var a = document.createElement('a');
        var blob = new Blob([content], {
          'type': contentType
        });
        a.href = window.URL.createObjectURL(blob);
        a.download = filename;
      }

      return service;
    }])
});
