define(['angular', 'ui.router',], function(angular) {

  'use strict';

  var module = angular.module('app.adminusers', ['ui.router']);

  module.config(function($stateProvider) {
    $stateProvider
      .state('adminusers', {
        url: '/admin-users',
        templateUrl: 'js/modules/admin/manage-users.html',
        controller: 'AdminManageUsersController',
      })
  });

  module.controller('AdminManageUsersController', function($scope, userManager, modalService, utilService, toastr) {

    utilService
      .rpcRun(
        'get_user_summaries')
      .then(function(response) {
        $scope.users = response.data.users;
      });

    $scope.deleteUser = function(user) {
      modalService.confirm(
        function() {
          utilService
            .rpcRun('delete_user', [user.id])
            .then(function(response) {
              toastr.success('User deleted!');
              $scope.users = _($scope.users).filter(function(u) {
                return u.id != user.id;
              });
            });
        },
        undefined,
        'Delete it',
        'Cancel',
        'Are you sure you want to delete this user? Note that all of his projects will be deleted too!', 'Warning!'
      );
    };
  });

  return module;

});
