define(['angular' ], function (angular) {
  'use strict';

  /**
   * This is a key service that provides access to the webserver.
   * As the web-server is essentially an adaptor to the optima model,
   * where the database is essentially a file-store of old models,
   * the approach here is to provide an RPC service directly into
   * the python `dataio` module.
   *
   * The interface of RPC services are JSON-data structures, i.e.
   * numbers, strings, lists, and dictionaries.
   *
   * Due to an inherent security concern of Javascript, the web-server
   * only returns JSON-data structures wrapped in a dictionary.
   *
   * There are 4 routines that cover most situations (the exception
   * is some legacy calls in user/user-api-service):
   *
   * 1. rpcRun - to run functions that only require JSON parameters and
   *    return JSON parameters
   *
   * 2. rpcDownload - to fetch files from the server, the corresponding
   *    python function must return a full pathname, the relative
   *    filename is returned and used to save the file on the webclient's
   *    computer
   *
   * 3. rpcUpload - to send files to the web-server. this will open a dialog
   *    box, with optional extension filtering. The selected file will
   *    be sent to the web-server and the called function will receive the
   *    filename as the first parameter, and the rest of the parameters after that.
   *    This will return the function results
   *
   * 4. rpcAsyncRun - in the webserver, async tasks are implemented in
   *    a different module that interacts with the celery task server.
   *    Functions that need to account are accessed through rpcAsyncRun
   *    rather than rpcRun. There are a handful of such functions:
   *      - check_task
   *      - check_if_task_started
   *      - launch_task - this is a special function that in turns
   *        launches all the async task in the tasks.py module
   *        the parameter structure is:
   *          [taskId, python_proc_name, [args]]
   *
   */

  return angular.module('app.rpc-service', [])

    .factory('rpcService',
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
        tag += " multiple>";
        var deferred = $q.defer();
        angular
          .element(tag)
          .change(function(event) {
            promise = new Promise(function (resolve, reject) {resolve('');});

            consoleLogCommand("upload-files", name, "files:", this.files);
            for (var i = 0; i < this.files.length; i++) {
              var currentFile = this.files[i];
              promise = promise.then(
                function(response) {
                  return $upload.upload({
                    url: '/api/upload',
                    fields: {
                      name: name,
                      args: JSON.stringify(args),
                      kwargs: JSON.stringify(kwargs)
                    },
                    file: currentFile
                  });
                },
                function (response) {
                  deferred.reject(response);
                }
              );
            }

            promise.then(
              function(response) {
                deferred.resolve(response);
              },
              function(response) {
                deferred.reject(response);
              }
            );
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
