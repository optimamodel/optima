define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';
  module.controller('AdminManageUsersController', function (
      $scope, $http, users, userManager, modalService, toastr) {
    $scope.users = users.data.users;

    $scope.deleteUser = function (user) {
      modalService.confirm(function(){
        $http.delete('/api/user/' + user.id).then(function(){
          toastr.success('User deleted!');
          $scope.users = _($scope.users).filter(function(u){
            return u.id != user.id;
          });
        });
        }, undefined, 'Delete it', 'Cancel',
        'Are you sure you want to delete this user? Note that all of his projects will be deleted too!', 'Warning!');
    };
  });
});
