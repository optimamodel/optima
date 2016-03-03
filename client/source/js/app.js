define([
  'angular',
  'angular-loading-bar',
  'angular-messages',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  './config',
  './modules/contact/index',
  './modules/help/index',
  './modules/auth/index',
  './modules/analysis/index',
  './modules/admin/index',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/file-upload-service',
  './modules/validations/less-than-directive',
  './modules/common/local-storage-service',
  './modules/common/normalise-height-directive',
  './modules/validations/more-than-directive',
  './modules/validations/file-required-directive',
  './modules/common/chart-toolbar-directive',
  './modules/d3-charts/index',
  './modules/graphs/index',
  './modules/home/index',
  './modules/model/index',
  './modules/project/index',
  './modules/project-set/index',
  './modules/user-manager/index',
  './modules/ui/modal/modal-service',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
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
    'app.common.normalise-height',
    'app.constants',
    'app.d3-charts',
    'app.graphs',
    'app.home',
    'app.validations.less-than',
    'app.local-storage',
    'app.model',
    'app.project-set',
    'app.validations.more-than',
    'app.validations.file-required',
    'app.project',
    'app.chart-toolbar',
    'app.ui',
    'app.ui.modal',
    'app.ui.spreadsheet-upload-hint',
    'app.user-manager',
    'ngMessages',
    'ui.bootstrap',
    'ui.router'
  ])

    .config(function ($httpProvider) {
      $httpProvider.interceptors.push(function ($q, $injector) {
        return {
          responseError: function (rejection) {
            if (rejection.status === 401 && rejection.config.url !== '/api/users/current') {
              // Redirect them back to login page
              location.href = '/#/login';

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

    .run(function ($rootScope, $state, UserManager, activeProject, modalService) {

      // if (navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') !== -1) {
      //   modalService.inform(
      //     function () {
      //       window.location.href = 'https://www.google.com/chrome/browser/desktop/';
      //     },
      //     'Download Google Chrome',
      //     'Internet Explorer is not supported. Please use Firefox or Chrome instead.', 'Your browser is not supported!');
      // }

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
