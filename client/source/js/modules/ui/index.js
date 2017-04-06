define([
    'angular',
    './menu-directive',
    './modal-service',
    '../project/index',
    '../user/user-manager-service'
  ],
  function (angular) {
    'use strict';
    var module = angular
      .module(
        'app.ui', [
          'app.project',
          'app.ui.modal',
          'app.ui.menu'
        ])
      .controller(
        'MainCtrl',
        function ($scope, $state, userManager, projectApi) {
          $scope.user = userManager.user;
          $scope.state = $state;
          $scope.userLogged = function () { return userManager.isLoggedIn; };
          $scope.projectApi = projectApi;
          $scope.projects = projectApi.projects;
          $scope.changeProject = function(projectId) {
            projectApi.setActiveProjectId(projectId);
          };
        });
    return module;
  }
);
