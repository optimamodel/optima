/**
 * activeProject is a factory that can set what's the project that should be currently in use by the UI
 * and tell you if there is any.
 */

define([
  'angular',
  '../common/local-storage-service'
], function (angular) {
  'use strict';

  return angular.module('app.active-project', [
    'app.local-storage'
  ])
    .factory('activeProject', function ($http, localStorage, User) {

      var project = {
        setValue: function (name) {
          project.name = name;
          $http.defaults.headers.common.project = name;
          localStorage.project = name;
        },
        isSet: function() {
          debugger
          return (project.name !== null && project.name !== undefined);
        }
      };

      return project;

    });

});
