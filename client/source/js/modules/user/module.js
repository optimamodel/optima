define(['angular', '../common/project-api-service'], function (angular) {
  'use strict';

  return angular.module('app.user', ['app.common.project-api-service'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('login', {
          url: '/login',
          onEnter: function ($state, userManager) {
            if (userManager.isLoggedIn) {
              $state.go('home');
            }
          },
          templateUrl: 'js/modules/user/login.html' ,
          controller: 'LoginController'
        })
        .state('register', {
          url: '/register',
          onEnter: function ($state, userManager) {
            if (userManager.isLoggedIn) {
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
