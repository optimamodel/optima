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
            debugger
            console.warn('activeProject.setValue is deprecated. Use setProjectFor(projectName, user) instead.');
            project.name = name;
            $http.defaults.headers.common.project = name;
            localStorage.project = name;
          },
          setActiveProjectFor: function (projectName, user) { 
            // Sets the active project to be projectName for the given user.
            project.name = projectName;
            $http.defaults.headers.common.project = project.name;
            localStorage[project.getProjectKeyFor(user)] = project.name;
          },
          loadProjectFor: function (user) { 
            // Load the active project for the given user.
            // Do nothing if no project found for that user.
            if(!project.hasProjectFor(user)) { return }
            project.name = project.getProjectFor(user);
            $http.defaults.headers.common.project = project.name;
          },
          getProjectKeyFor: function (user) {
            // Answers the key used to locally store this project as active for the given user.
            return 'activeProjectFor:'+ user.email;
          },
          getProjectFor: function (user) {
            return localStorage[project.getProjectKeyFor(user)];
          },
          ifActiveResetFor: function (projectName, user) {
            // If projectName is active, reset it for the given user.
            if (activeProject.name === projectName) {
              activeProject.setActiveProjectFor('', user);};
          },
          resetFor: function (user) { 
            // Resets the projectName as the active project for the given user.
            debugger
            delete project.name;
            localStorage.removeItem(project.getProjectKeyFor(user));
          },  
          isSet: function() {
            return (project.name !== null && project.name !== undefined);
          },
          hasProjectFor: function (user) {
            // Answers true if there is a local project stored for the given user.
            var foundOrNot = project.getProjectFor(user);
            return foundOrNot !== null && foundOrNot !== undefined;
          }
        };

        return project;

    }]);

});
