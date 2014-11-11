define([
  'angular',
  'angular-nvd3',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  './config',
  './modules/about/index',
  './modules/auth/index',
  './modules/analyses/index',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/save-graph-as-directive',
  './modules/d3-charts/index',
  './modules/forecasts/index',
  './modules/graphs/index',
  './modules/help/index',
  './modules/home/index',
  './modules/import-export/index',
  './modules/model/index',
  './modules/optimization/index',
  './modules/playground/index',
  './modules/project/index',
  './modules/user-manager/index',
  './modules/results/index',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
    'angularFileUpload',
    'app.about',
    'app.auth',
    'app.active-project',
    'app.analyses',
    'app.common.form-input-validate',
    'app.constants',
    'app.d3-charts',
    'app.forecasts',
    'app.graphs',
    'app.help',
    'app.home',
    'app.import-export',
    'app.model',
    'app.optimization',
    'app.playground',
    'app.project',
    'app.results',
    'app.save-graph-as',
    'app.ui',
    'app.user-manager',
    'nvd3',
    'ui.bootstrap',
    'ui.router'
  ])

    .config(function ($httpProvider) {
      var logoutUserOn401 = ['$q', function ($q) {
        var success = function (response) {
          return response;
        };

        var error = function (response) {
          if (response.status === 401 && response.config.url !== '/api/users/current') {
            // Redirect them back to login page
            location.href = '/#/login';

            return $q.reject(response);
          } else {
            if (response.data.message) {
              alert(response.data.message);
            }

            return $q.reject(response);
          }
        };

        return function (promise) {
          return promise.then(success, error);
        };
      }];

      $httpProvider.responseInterceptors.push(logoutUserOn401);
    })

    .config(function ($urlRouterProvider) {
      $urlRouterProvider.otherwise('/');
    })

    .run(function ($rootScope, $state, UserManager) {
      if (window.user) {
        UserManager.set(window.user);
        delete window.user;
      }

      var isStatePublic = function (stateName) {
        var publicStates = ['about', 'contact', 'help', 'login', 'register'];

        return publicStates.indexOf(stateName) !== -1;
      };

      $rootScope.$on('$stateChangeStart', function (event, to) {
        if (!UserManager.isLoggedIn && !isStatePublic(to.name)) {
          event.preventDefault();
          $state.go('login');
        }
      });
    });

});
