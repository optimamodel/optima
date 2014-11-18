define([
  'angular',
  '../common/local-storage-service'
], function (angular) {
  'use strict';

  return angular.module('app.active-project', [
    'app.local-storage'
  ])
    .factory('activeProject', function ($http, localStorage) {

      var project = {
        setValue: function (name) {
          project.name = name;
          $http.defaults.headers.common.project = name;
          localStorage.project = name;
        }
      };

      return project;

    });

});
