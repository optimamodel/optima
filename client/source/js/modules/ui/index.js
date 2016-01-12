define([
  'angular',
  './editable/index',
  './menu/index',
  './spreadsheet-upload-hint/index',
  './modal/modal-service',
  '../common/file-upload-service',
  '../common/active-project-service',
  '../user-manager/index'
], function (angular) {
  'use strict';

  return angular.module('app.ui', [
    'app.active-project',
    'app.ui.editable',
    'app.ui.modal',
    'app.common.file-upload',
    'app.ui.menu'
  ])
  .controller('MainCtrl', function ($scope, $state, activeProject, UserManager, modalService, fileUpload) {
    $scope.user = UserManager.data;
    $scope.userLogged = function () {
      return UserManager.isLoggedIn;
    };
    $scope.activeProject = activeProject;
  });
});
