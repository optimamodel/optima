define([
  'angular',
  'angular-loading-bar',
  'angular-nvd3',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  './config',
  './modules/contact/index',
  './modules/auth/index',
  './modules/analysis/index',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/local-storage-service',
  './modules/common/save-graph-as-directive',
  './modules/d3-charts/index',
  './modules/graphs/index',
  './modules/home/index',
  './modules/import-export/index',
  './modules/model/index',
  './modules/project/index',
  './modules/user-manager/index',
  './modules/results/index',
  './modules/ui/modal/modal-service',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
    'angularFileUpload',
    'angular-loading-bar',
    'app.contact',
    'app.auth',
    'app.active-project',
    'app.analysis',
    'app.common.form-input-validate',
    'app.constants',
    'app.d3-charts',
    'app.graphs',
    'app.home',
    'app.import-export',
    'app.local-storage',
    'app.model',
    'app.project',
    'app.results',
    'app.save-graph-as',
    'app.ui',
    'app.ui.modal',
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
            var message = response.data.message || response.data.exception;
            if (message) {
              alert(message);
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

    .run(function ($rootScope, $state, UserManager, localStorage, activeProject) {
      if (window.user) {
        UserManager.set(window.user);
        delete window.user;
      }
      if (localStorage.project) {
        activeProject.setProjectFor(localStorage.project,UserManager.data);
      }

      var isStatePublic = function (stateName) {
        var publicStates = ['contact', 'login', 'register'];

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
