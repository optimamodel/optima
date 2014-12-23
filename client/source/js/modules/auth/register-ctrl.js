define(['./module'], function (module) {
  'use strict';

  return module.controller('RegisterController', function ($scope, $window, User) {

    $scope.error = false;

    $scope.register = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.RegisterForm.$invalid) {
        return;
      }

      $scope.error = false;

      User.create({
        name: $scope.fullName,
        email: $scope.email,
        password: $scope.password
      },
        // success
        function (response) {
          if (response.status) {
            // error returned
            $scope.error = response.status;

            if ( response.status == "This email is already in use" ) {

              // show css error tick to email field
              $scope.RegisterForm.email.$invalid = true;
              $scope.RegisterForm.email.$valid = false;
              $scope.$broadcast('form-input-check-validity');
            }
          } else if (response.email) {
            // success
            $window.location = '/';
          }
        },
        // error
        function () {
          $scope.error = 'Server feels bad. Please try again in a bit';
        }
      );
    };

  });

});
