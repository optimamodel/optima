define(['./module'], function (module) {
  'use strict';

  return module.controller('LoginController', function ($scope, $window, User) {

    $scope.error = false;

    $scope.login = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.LogInForm.$invalid) {
        return;
      }

      $scope.error = false;

      User.login({
        email: $scope.email,
        password: $scope.password
      },
        // success
        function (user) {
          $window.location = '/';
        },
        // error
        function () {
          $scope.error = true;
        }
      );
    };

  });

});
