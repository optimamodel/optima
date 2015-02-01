define([
  'angular',
  'angular-loading-bar',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  './config',
  './modules/contact/index',
  './modules/auth/index',
  './modules/analysis/index',
  './modules/admin/index',
  './modules/common/active-project-service',
  './modules/common/form-input-validate-directive',
  './modules/common/file-upload-service',
  './modules/validations/less-than-directive',
  './modules/common/local-storage-service',
  './modules/validations/more-than-directive',
  './modules/common/save-graph-as-directive',
  './modules/d3-charts/index',
  './modules/graphs/index',
  './modules/home/index',
  './modules/model/index',
  './modules/project/index',
  './modules/user-manager/index',
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
    'app.admin',
    'app.common.form-input-validate',
    'app.common.file-upload',
    'app.constants',
    'app.d3-charts',
    'app.graphs',
    'app.home',
    'app.validations.less-than',
    'app.local-storage',
    'app.model',
    'app.validations.more-than',
    'app.project',
    'app.save-graph-as',
    'app.ui',
    'app.ui.modal',
    'app.user-manager',
    'ui.bootstrap',
    'ui.router'
  ])

    .config(function ($httpProvider) {
      var logoutUserOn401 = ['$q', '$injector', function ($q, $injector) {
        var success = function (response) {
          return response;
        };

        var error = function (response) {
          if (response.status === 401 && response.config.url !== '/api/users/current') {
            // Redirect them back to login page
            location.href = '/#/login';

            return $q.reject(response);
          } else {
            var message, errorText;
            if (response.data.message || response.data.exception) {
              message = "Something went wrong. Please try again or contact the support team.";
              errorText = response.data.message || response.data.exception;
            } else {
              message = 'Sorry, but our servers feel bad right now. Please, give them some time to recover or contact the support team.';
            }
            var modalService = $injector.get('modalService');
            modalService.inform(
              function () {},
              'Okay',
              message,
              'Upload Error',
              errorText
            );

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

    .run(function ($rootScope, $state, UserManager, localStorage, activeProject, modalService) {

      if (navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') !== -1) {
        modalService.inform(
            function () {
              window.location.href = 'https://www.google.com/chrome/browser/desktop/';
            },
            'Download Google Chrome',
            'Internet Explorer is not supported. Please use Firefox or Chrome instead.', 'Your browser is not supported!');
      }

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
