/**
 * activeProject is a factory that can set what's the project that should be currently in use by the UI
 * and tell you if there is any.
 */

// todo: since now we do not keep project open after user session is complete, it makes sense to remove it from local-storage to cookie-storage

define(['angular', '../common/local-storage-polyfill'], function (angular) {
  'use strict';

  return angular.module('app.active-project', ['app.local-storage'])

    .factory('activeProject', [
      '$http', 'localStorage', 'userManager',
      function ($http, localStorage, userManager) {

        var activeProject = {
          project: {}
        };

        _.assign(activeProject, {
          setActiveProjectId: function (projectId) {
            // Sets the active project to be projectName for the given user.
            activeProject.project.name = '';
            activeProject.project.id   = projectId;
            var str = JSON.stringify(activeProject.project);
            localStorage[activeProject.getProjectKeyFor(userManager.user)] = str;
          },
          loadProjectFor: function (user) { 
            // Load the active project for the given user.
            // Do nothing if no project found for that user.`
            if(!activeProject.hasProjectFor(user)) { return; }
            var loaded_project = JSON.parse(activeProject.getProjectFor(user));
            activeProject.project.name = loaded_project.name;
            activeProject.project.id = loaded_project.id;
          },
          getProjectKeyFor: function (user) {
            // Answers the key used to locally store this project as active for the given user.
            return 'activeProjectFor:'+ user.id;
          },
          getProjectFor: function (user) {
            return localStorage[activeProject.getProjectKeyFor(user)];
          },
          getProjectForCurrentUser: function (user) {
            var openProjectStr = activeProject.getProjectFor(userManager.user);
            return openProjectStr ? JSON.parse(openProjectStr) : void 0;
          },
          getProjectIdForCurrentUser: function (user) {
            var openProjectStr = activeProject.getProjectFor(userManager.user);
            var openProject = openProjectStr ? JSON.parse(openProjectStr) : void 0;
            return openProject ? openProject.id : void 0;
          },
          ifActiveResetFor: function (projectId, user) {
            if (activeProject.project.id === projectId) {
              activeProject.resetFor(user);
            }
          },
          resetFor: function (user) {
            // Resets the projectName as the active project for the given user.
            delete activeProject.project.name;
            delete activeProject.project.id;
            localStorage.removeItem(activeProject.getProjectKeyFor(user));
          },
          removeProjectForUserId: function (userId) {
            localStorage.removeItem('activeProjectFor:' + userId);
          },
          isSet: function() {
            return (activeProject.project.name !== null
              && activeProject.project.name !== undefined
              && activeProject.project.id !== null
              && activeProject.project.id !== undefined);
          },
          hasProjectFor: function (user) {
            // Answers true if there is a local project stored for the given user.
            var foundOrNot = activeProject.getProjectFor(user);
            if (foundOrNot !== null && foundOrNot !== undefined) {
              try {
                JSON.parse(foundOrNot);
                return true;
              } catch (exception) {
                return false;
              }
            }
          }
        });

        return activeProject;

    }]);

});
