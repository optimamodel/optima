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
    .factory('activeProject', [ 
      '$http', 'localStorage',
      function ($http, localStorage) {
        var project = {
          setValue: function (name) {  // deprecated method 
            console.warn('activeProject.setValue is deprecated. Use setProjectFor(projectName, user) instead.');
            project.name = name;
            $http.defaults.headers.common.project = name;
            localStorage.project = name;
          },
          setProjectFor: function (projectName, user) { 
            // Sets projectName as the active project for the given user 
            debugger
            project.name = projectName;
            $http.defaults.headers.common.project = projectName;
            localStorage.project = projectName;
          },          
           resetFor: function (user) { 
            // Resets the projectName as the active project for the given user 
            debugger
            project.name = projectName;
            $http.defaults.headers.common.project = projectName;
            localStorage.project = projectName;
          },  
         isSet: function() {
            debugger
            return (project.name !== null && project.name !== undefined);
          }
        };

        return project;

    }]);

});
