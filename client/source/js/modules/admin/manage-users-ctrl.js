define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';
  module.controller('AdminManageUsersController', function ($scope, $http, users, UserManager, modalService) {
    $scope.users = _(users.data.users).filter(function (u) {
      return u.id != UserManager.data.id;
    });

    $scope.deleteUser = function (user) {
      modalService.confirm(function(){
        $http.delete('/api/user/delete/' + user.id).then(function(){
          modalService.inform(undefined,undefined, 'User deleted!');
          $scope.users = _($scope.users).filter(function(u){
            return u.id != user.id;
          });
        });
        }, undefined, 'Delete it', 'Cancel',
        'Are you sure you want to delete this user? Note that all of his projects will be deleted too!', 'Warning!');
    };
  });
});
