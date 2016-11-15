define([
  'angular',
  'ng-loading-bar',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  'tooltip',
  'rzModule',
  './modules/mpld3-charts/index',
  './modules/contact/index',
  './modules/help/index',
  './modules/auth/index',
  './modules/analysis/index',
  './modules/admin/index',
  './modules/common/global-poller-service.js',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/file-upload-service',
  './modules/common/local-storage-service',
  './modules/home/index',
  './modules/model/index',
  './modules/project/index',
  './modules/portfolio/index',
  './modules/programs/index',
  './modules/user-manager/index',
  './modules/ui/modal/modal-service',
  './modules/ui/index'
], function (angular) {

  'use strict';

  return angular

    .module(
      'app',
      [
        'angularFileUpload',
        'angular-loading-bar',
        'app.contact',
        'app.help',
        'app.auth',
        'app.active-project',
        'app.analysis',
        'app.admin',
        'app.common.form-input-validate',
        'app.common.file-upload',
        'app.common.global-poller-service',
        'app.mpld3-charts',
        'app.home',
        'app.local-storage',
        'app.model',
        'app.programs',
        'app.project',
        'app.portfolio',
        'app.ui',
        'app.ui.modal',
        'app.user-manager',
        'ui.bootstrap',
        'ui.router',
        'tooltip.module',
        'rzModule',
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

    .run(function ($rootScope, $state, UserManager, activeProject) {

      if (window.user) {
        UserManager.set(window.user);
        delete window.user;
      }

      // Set the active project if any
      activeProject.loadProjectFor(UserManager.data);

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
