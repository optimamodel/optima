define([
    'angular',
    './menu/index',
    './modal/modal-service',
    '../common/file-upload-service',
    '../common/active-project-service',
    '../user/index'
  ],
  function (angular) {
    'use strict';
    var module = angular
      .module(
        'app.ui', [
          'app.active-project',
          'app.ui.modal',
          'app.common.file-upload',
          'app.ui.menu'
        ])
      .controller(
        'MainCtrl',
        function ($scope, $state, activeProject, UserManager) {
          $scope.user = UserManager.currentUser;
          $scope.state = $state;
          $scope.userLogged = function () { return UserManager.isLoggedIn; };
          $scope.activeProject = activeProject;
         });
    return module;
  }
);
