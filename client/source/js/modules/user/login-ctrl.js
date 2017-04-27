define(['./module', 'sha224/sha224'], function (module, SHA224) {

  'use strict';

  return module.controller('LoginController', function ($scope, $window, userApi, projectService) {

    $scope.error = '';

    $scope.login = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.LogInForm.$invalid) {
        return;
      }

      $scope.error = '';
      var hashed_password = SHA224($scope.password).toString();

      userApi
        .login(
          {
            username: $scope.username,
            password: hashed_password
          },
          // success
          function(user) {
            projectService.clearProjectForUserId(user.id);
            $window.location = './';
          },
          // error
          function (error) {
            if (error.status === 401) {
              $scope.error = 'Wrong username or password. Please check credentials and try again';
            } else {
              $scope.error = 'Server feels bad. Please try again in a bit';
            }
          }
        );
    };

  });

});
