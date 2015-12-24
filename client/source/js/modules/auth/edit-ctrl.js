define(['./module', '../sha224/sha224'], function (module, SHA224) {
  'use strict';

  return module.controller('EditController', function ($scope, $window, User, UserManager, $timeout) {

    $scope.error = false;

    const user = UserManager.data;
    $scope.username = user.username;
    $scope.displayName = user.displayName;
    $scope.email = user.email;
    $scope.password = '';

    $scope.update = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.EditForm.$invalid) {
        return;
      }

      $scope.error = false;

      var hashed_password = SHA224($scope.password).toString();

      User.update({
          username: $scope.username,
          password: hashed_password,
          displayName: $scope.displayName,
          email: $scope.email,
          id: user.id
        },
        // success
        function (response) {
          if (response.id) {
            $scope.success = 'User details successfully updated (reload page to see changes).';
            $timeout(function() {
              $scope.success = '';
            }, 5000);
          }
        },
        // error
        function (error) {
          $scope.error = error.data.reason;
          $timeout(function() {
            $scope.error = '';
          }, 5000);
          switch(error.status){
            case 409: // conflict: will be sent if the email already exists
              // show css error tick to email field
              $scope.EditForm.email.$invalid = true;
              $scope.EditForm.email.$valid = false;
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
