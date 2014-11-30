// ProjectOpenController deals with loading and removing projects

define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ProjectOpenController', function ($scope, $http, activeProject, localStorage, projects) {

    $scope.projects = projects.projects;

    /**
     * Opens an existing project using `name`
     *
     * Alerts the user if it cannot do it.
     */
    $scope.open = function (name) {
      $http.get('/api/project/open/' + name)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
            return;
          }
          activeProject.setValue(name);
        });
    };

    /**
     * Removes the project
     *
     * If the removed project is the active one it will reset it alerts the user
     * in case of failure.
     */
    var removeNoQuestionsAsked = function (name, index) {
      $http.delete('/api/project/delete/' + name)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
            return;
          }

          $scope.projects.splice(index, 1);

          if (activeProject.name === name) {
            activeProject.setValue('');
          }
        })
        .error(function () {
          alert('Could not remove the project');
        });
    };

    /**
     * Opens a dialog to ask the user for confirmation to remove the project and
     * removes the project if the user confirms.
     */
    $scope.remove = function ($event, name, index) {
      if ($event) { $event.preventDefault(); }
      if(confirm('Are you sure you want to permanently remove project "' + name + '"?')) {
        removeNoQuestionsAsked(name, index);
      }
    };
  });

});
