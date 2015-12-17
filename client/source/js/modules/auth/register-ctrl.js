define(['./module', '../sha224/sha224'], function (module, SHA224) {
  'use strict';

  return module.controller('RegisterController', function ($scope, $window, User) {

    $scope.error = false;

    $scope.register = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.RegisterForm.$invalid) {
        return;
      }

      $scope.error = false;

      var hashed_password = SHA224($scope.password).toString();

      User.create({
        username: $scope.userName,
        password: hashed_password,
        displayName: $scope.displayName,
        email: $scope.email
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
