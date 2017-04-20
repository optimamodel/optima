define(['angular' ], function (angular) {
  'use strict';

  /**
   * utility services until split off into own modules
   */

  return angular.module('app.util', [])

    .factory('util',
      ['$http', '$q', '$timeout', '$upload', function($http, $q, $timeout, $upload) {

      function consoleLogCommand(type, name, args, kwargs) {
        if (!args) {
          args = '';
        }
        if (!kwargs) {
          kwargs = '';
        }
        console.log("rpcService." + type + "." + name, args, kwargs);
      }

      function rpcRun(name, args, kwargs) {
        consoleLogCommand("run", name, args, kwargs)
        return $http.post(
          '/api/procedure', { name: name, args: args, kwargs: kwargs });
      }

      function rpcAsyncRun(name, args, kwargs) {
        consoleLogCommand("asyncRun", name, args, kwargs)
        return $http.post(
          '/api/task', { name: name, args: args, kwargs: kwargs });
      }

      function rpcDownload(name, args, kwargs) {
        consoleLogCommand("download", name, args, kwargs)
        var deferred = $q.defer();
        $http
          .post(
            '/api/download',
            {
              name: name,
              args: args,
              kwargs: kwargs
            },
            {
              responseType: 'blob'
            })
          .then(
            function(response) {
              var blob = new Blob([response.data]);
              var filename = response.headers().filename;
              saveAs(blob, (filename));
              var headers = response.headers();
              if (headers.data) {
                response.data = JSON.parse(headers.data);
              }
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function rpcUpload(name, args, kwargs, fileType) {
        consoleLogCommand("upload", name, args, kwargs, fileType);
        var tag = '<input type="file" ';
        if (fileType) {
          tag += 'accept="' + fileType + '" '
        }
        tag += ">";
        var deferred = $q.defer();
        angular
          .element(tag)
          .change(function(event) {
            $upload
              .upload({
                url: '/api/upload',
                fields: {
                  name: name,
                  args: JSON.stringify(args),
                  kwargs: JSON.stringify(kwargs)
                },
                file: event.target.files[0]
              })
              .then(
                function(response) {
                  deferred.resolve(response);
                },
                function(response) {
                  deferred.reject(response);
                });
          })
          .click();
        return deferred.promise;
      }

      function getUniqueName(name, otherNames) {
        var i = 0;
        var uniqueName = name;
        while (_.indexOf(otherNames, uniqueName) >= 0) {
          i += 1;
          uniqueName = name + ' (' + i + ')';
        }
        return uniqueName;
      }

      return {
        rpcRun: rpcRun,
        rpcAsyncRun: rpcAsyncRun,
        rpcDownload: rpcDownload,
        rpcUpload: rpcUpload,
        getUniqueName: getUniqueName
      };

    }]);

});
