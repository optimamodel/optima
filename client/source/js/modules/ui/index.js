define([
    'angular',
    './menu-directive',
    './modal-service',
    '../common/active-project-service',
    '../user/user-manager-service'
  ],
  function (angular) {
    'use strict';
    var module = angular
      .module(
        'app.ui', [
          'app.active-project',
          'app.ui.modal',
          'app.ui.menu'
        ])
      .controller(
        'MainCtrl',
        function ($scope, $state, activeProject, userManager, projectApi) {
          $scope.user = userManager.user;
          $scope.state = $state;
          $scope.userLogged = function () { return userManager.isLoggedIn; };
          $scope.activeProject = activeProject;
          $scope.projects = projectApi.projects;
          $scope.changeProject = function(projectId) {
            activeProject.setActiveProjectId(projectId);
          };
        });
    return module;
  }
);
