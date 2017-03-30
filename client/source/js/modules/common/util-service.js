define(['angular' ], function (angular) {
  'use strict';

  /**
   * utility services until split off into own modules
   */

  return angular.module('app.util', [])

    .factory('util', ['$http', '$timeout', function($http, $timeout) {

      function rpcRun(name, args, kwargs) {
        return $http.post(
          '/api/procedure', { name: name, args: args, kwargs: kwargs });
      }

      function rpcDownload(name, args, kwargs) {
        var payload = {name: name, args: args};
        $http
          .post(
            '/api/download', payload, {responseType: 'blob'})
          .then(function(response) {
            var blob = new Blob([response.data], {type: 'application/octet-stream'});
            saveAs(blob, (response.headers('filename')));
          });
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
        rpcDownload: rpcDownload,
        getUniqueName: getUniqueName
      };

    }]);

});
