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
          if (response.email) {
            // success
            $window.location = '/';
          }
        },
        // error
        function (error) {
          $scope.error = error.data.reason;
          switch(error.status){
            case 409: // conflict: will be sent if the email already exists
              // show css error tick to email field
              $scope.RegisterForm.email.$invalid = true;
              $scope.RegisterForm.email.$valid = false;
              $scope.$broadcast('form-input-check-validity');
              break;
            case 400:
              break;
            default:
              $scope.error = 'Server feels bad. Please try again in a bit';
          }
        }
      );
    };

  });

});
