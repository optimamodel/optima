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
        function ($scope, $state, activeProject, tmpHelpService, userManager) {
          $scope.user = userManager.user;
          $scope.state = $state;
          $scope.userLogged = function () { return userManager.isLoggedIn; };
          $scope.activeProject = activeProject;
          $scope.openHelp = tmpHelpService;
         });
    return module;
  }
);
