define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.user', ['app.active-project'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('login', {
          url: '/login',
          onEnter: function ($state, UserManager) {
            if (UserManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/login.html' ,
          controller: 'LoginController'
        })
        .state('register', {
          url: '/register',
          onEnter: function ($state, UserManager) {
            if (UserManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/register.html' ,
          controller: 'RegisterController'
        })
        .state('edit', {
          url: '/edit',
          templateUrl: 'js/modules/user/edit.html' ,
          controller: 'EditController'
        });
    });

});
