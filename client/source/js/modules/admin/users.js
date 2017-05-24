define(['angular', 'ui.router',], function(angular) {

  'use strict';

  var module = angular.module('app.admin-users', ['ui.router']);

  module.config(function($stateProvider) {
    $stateProvider
      .state('adminusers', {
        url: '/admin-users',
        templateUrl: 'js/modules/admin/users.html',
        controller: 'AdminManageUsersController',
      })
  });

  module.controller('AdminManageUsersController', function($scope, userManager, modalService, rpcService, toastr) {

    rpcService
      .rpcRun(
        'get_user_summaries')
      .then(function(response) {
        $scope.users = response.data.users;
      });

    $scope.deleteUser = function(user) {
      modalService.confirm(
        function() {
          rpcService
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

    $scope.grantAdmin = function(user) {
      modalService.confirm(
        function() {
          rpcService
            .rpcRun('grant_admin', [user.id])
            .then(function(response) {
              toastr.success('Admin rights granted!');
              $scope.users = _($scope.users).filter(function(u) {
                return u.id != user.id;
              });
            });
        },
        undefined,
        'Make admin',
        'Cancel',
        'Are you sure you want to make this user an admin? With great power comes great responsibility!', 'Warning!'
      );
    };

    $scope.revokeAdmin = function(user) {
      modalService.confirm(
        function() {
          rpcService
            .rpcRun('revoke_admin', [user.id])
            .then(function(response) {
              toastr.success('Admin rights revoked!');
              $scope.users = _($scope.users).filter(function(u) {
                return u.id != user.id;
              });
            });
        },
        undefined,
        'Remove admin',
        'Cancel',
        'Are you sure you want to remove admin rights for this user? Were their crimes that serious?', 'Warning!'
      );
    };
  });

  return module;

});
