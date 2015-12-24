define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.auth', [])
    .config(function ($stateProvider) {
      $stateProvider
        .state('login', {
          url: '/login',
          onEnter: function ($state, UserManager) {
            if (UserManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/auth/login.html' ,
          controller: 'LoginController'
        })
        .state('register', {
          url: '/register',
          onEnter: function ($state, UserManager) {
            if (UserManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/auth/register.html' ,
          controller: 'RegisterController'
        })
        .state('edit', {
          url: '/edit',
          templateUrl: 'js/modules/auth/edit.html' ,
          controller: 'EditController'
        });
    });

});
