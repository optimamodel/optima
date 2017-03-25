define([
  'angular',
  'ng-loading-bar',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  'tooltip',
  'rzModule',
  './modules/charts/index',
  './modules/user/feedback-ctrl',
  './modules/user/help-ctrl',
  './modules/user/index',
  './modules/analysis/index',
  './modules/admin/index',
  './modules/common/global-poller-service',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/local-storage-polyfill',
  './modules/calibration/index',
  './modules/project/index',
  './modules/geospatial/index',
  './modules/programs/index',
  './modules/user/user-manager-service',
  './modules/ui/modal-service',
  './modules/ui/index'
], function (angular) {

  'use strict';

  return angular

    .module(
      'app',
      [
        'angularFileUpload',
        'angular-loading-bar',
        'ui.bootstrap',
        'ui.router',
        'tooltip.module',
        'rzModule',
        'app.contact',
        'app.help',
        'app.user',
        'app.active-project',
        'app.analysis',
        'app.admin',
        'app.common.form-input-validate',
        'app.common.global-poller',
        'app.charts',
        'app.local-storage',
        'app.model',
        'app.programs',
        'app.project',
        'app.geospatial',
        'app.ui',
        'app.ui.modal',
        'app.user-manager'
      ])

    .config(function ($httpProvider) {
      $httpProvider.interceptors.push(function ($q, $injector) {
        return {
          responseError: function (rejection) {
            if (rejection.status === 401 && rejection.config.url !== '/api/users/current') {
              // Redirect them back to login page
              location.href = './#/login';

              return $q.reject(rejection);
            } else {
              var message, errorText;
              if (rejection.data && (rejection.data.message || rejection.data.exception || rejection.data.reason)) {
                message = 'Something went wrong. Please try again or contact the support team.';
                errorText = rejection.data.message || rejection.data.exception || rejection.data.reason;
              } else {
                message = 'Sorry, but our servers feel bad right now. Please, give them some time to recover or contact the support team.';
              }
              var modalService = $injector.get('modalService');
              modalService.inform(angular.noop, 'Okay', message, 'Server Error', errorText);

              return $q.reject(rejection);
            }
          }
        };
      });
    })

    .config(function ($urlRouterProvider) {
      $urlRouterProvider.otherwise('/');
    })

    .run(function ($rootScope, $state, userManager, activeProject) {

      /**
       * an injector has been run in main.js before app.js to fetch
       * the current user and stored in window.user, this will be
       * used to build the app in the first run
       */
      if (window.user) {
        userManager.setUser(window.user);
        delete window.user;
      }

      // Set the active project if any
      activeProject.loadProjectFor(userManager.user);

      function isStatePublic(stateName) {
        var publicStates = ['contact', 'login', 'register'];
        return publicStates.indexOf(stateName) !== -1;
      }

      $rootScope.$on('$stateChangeStart', function (event, to) {
        if (!userManager.isLoggedIn && !isStatePublic(to.name)) {
          event.preventDefault();
          $state.go('login');
        }
      });
    });

});
