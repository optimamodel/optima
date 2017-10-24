define(['angular', 'sha224/sha224',  '../../version'], function (angular, SHA224, version) {


  'use strict';

  var module = angular.module('app.user', []);

  /**
   * Directive-based hack for automatically filled forms of sign in
   * <tag saved-login-form="ngModel">
   */
  module.directive('savedLoginForm', function ($timeout) {
    return {
      require: 'ngModel',
      link: function (scope, elem, attr, ngModel) {
        var origVal = elem.val();
        $timeout(function () {
          var newVal = elem.val();
          if (ngModel.$pristine && origVal !== newVal) {
            ngModel.$setViewValue(newVal);
          }
        }, 500);
      }
    };
  });

  
  /**
   * Defines all the user-based pages, their states and their controllers
   * login, register, edit, feedback, help
   */
  
  module.config(function ($stateProvider) {
      $stateProvider
        .state('login', {
          url: '/login',
          onEnter: function ($state, userManager) {
            if (userManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/login.html?cacheBust=xxx' ,
          controller: 'LoginController'
        })
        .state('register', {
          url: '/register',
          onEnter: function ($state, userManager) {
            if (userManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/register.html?cacheBust=xxx' ,
          controller: 'RegisterController'
        })
        .state('devregister', {
          url: '/devregister',
          onEnter: function ($state, userManager) {
            if (userManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/devregister.html?cacheBust=xxx' ,
          controller: 'DevRegisterController'
        })		
        .state('edit', {
          url: '/edit',
          templateUrl: 'js/modules/user/edit.html?cacheBust=xxx' ,
          controller: 'EditController'
        })
        .state('feedback', {
          url: '/feedback',
          templateUrl: 'js/modules/user/feedback.html?cacheBust=xxx'
        })
        .state('help', {
          url: '/help',
          templateUrl: 'js/modules/user/help.html?cacheBust=xxx',
          controller: function ($scope) {
            $scope.version = version;
          }
        });
    });


  /**
   * Controllers for edit/login/register pages
   */

  module.controller(
    'EditController',
    function ($scope, $window, userApi, userManager, $timeout) {

    $scope.error = false;

    const user = userManager.user;
    $scope.username = user.username;
    $scope.displayName = user.displayName;
    $scope.email = user.email;
    $scope.password = '';
    $scope.country = user.country;
    $scope.organization = user.organization;
    $scope.position = user.position;

    $scope.update = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.EditForm.$invalid) {
        return;
      }

      $scope.error = false;

      var hashed_password = SHA224($scope.password).toString();

      // Use '' as the hashed password if we don't want to update the password.
      if ($scope.password == '') {
        hashed_password = ''
      }

      userApi.update({
          username: $scope.username,
          password: hashed_password,
          displayName: $scope.displayName,
          email: $scope.email,
          country: $scope.country,
          organization: $scope.organization,
          position: $scope.position,	  
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


  module.controller(
    'LoginController',
    function ($scope, $window, userApi, projectService) {

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

  
  module.controller(
    'RegisterController',
    function ($scope, $window, userApi, modalService) {

    $scope.error = false;
	
	$scope.termsAccepted = false;

    $scope.register = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.RegisterForm.$invalid) {
        return;
      }

      $scope.error = false;  

      var hashed_password = SHA224($scope.password).toString();

      userApi.create({
        username: $scope.username,
        password: hashed_password,
        displayName: $scope.displayName,
        email: $scope.email,
        country: $scope.country,
        organization: $scope.organization,
        position: $scope.position
      },
        // success
        function (response) {
          if (response.username) {
            // success
            $window.location = './#/login';
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
	
	$scope.spawnTerms = function () {
      modalService.termsAndConditions();
	}

  });
  
  module.controller(
    'DevRegisterController',
    function ($scope, $window, userApi) {

    $scope.error = false;

    $scope.register = function () {
      $scope.$broadcast('form-input-check-validity');

      if ($scope.RegisterForm.$invalid) {
        return;
      }

      $scope.error = false;

      var hashed_password = SHA224($scope.password).toString();

      userApi.create({
        username: $scope.username,
        password: hashed_password,
        displayName: $scope.displayName,
        email: $scope.email
      },
        // success
        function (response) {
          if (response.username) {
            // success
            $window.location = './#/login';
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
  
  return module;

});
