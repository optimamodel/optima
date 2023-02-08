define(['angular', 'ui.router',], function(angular) {

  'use strict';

  var module = angular.module('app.admin-users', ['ui.router']);

  module.config(function($stateProvider) {
    $stateProvider
      .state('adminusers', {
        url: '/admin-users',
        templateUrl: 'js/modules/admin/users.html?cacheBust=xxx',
        controller: 'AdminManageUsersController',
      })
  });

  module.controller('AdminManageUsersController', function($scope, userManager, modalService, rpcService, toastr) {

    $scope.refresh = function () {
      rpcService
        .rpcRun(
          'get_user_summaries')
        .then(function (response) {
          $scope.users = response.data.users;
        });
    };

    $scope.refresh();

    $scope.grantAdmin = function(user) {
      modalService.confirm(
        function() {
          rpcService
            .rpcRun('grant_admin', [user.id])
            .then(function(response) {
              toastr.success('Admin rights granted!');
              $scope.refresh();
            });
        },
        undefined,
        'Yes: sudo make me a sandwich',
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
              $scope.refresh();
            });
        },
        undefined,
        'Yes, revoke admin',
        'Cancel',
        'Are you sure you want to revoke admin rights for this user? Were their crimes that serious?', 'Warning!'
      );
    };

    $scope.resetPassword = function(user) {
      modalService.confirm(
        function() {
          rpcService
            .rpcRun('reset_password', [user.id])
            .then(function(response) {
              console.log('reset passsword response:',response)
              toastr.success('Password reset to "optima"!');
            });
        },
        undefined,
        'Yes, reset password',
        'Cancel',
        'Are you sure you want to reset the password to default for this user?', 'Warning!'
      );
    };

    $scope.deleteUser = function(user) {
      modalService.confirm(
        function() {
          rpcService
            .rpcRun('delete_user', [user.id])
            .then(function(response) {
              toastr.success('User deleted!');
              $scope.refresh();
            });
        },
        undefined,
        'Delete it',
        'Cancel',
        'Are you sure you want to delete this user? Note that all of her projects will be deleted too!', 'Warning!'
      );
    };
  });

  return module;

});
