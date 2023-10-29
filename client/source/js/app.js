define([
  // these are the explicit references to the modules
  // required by app those from third parties are
  // referenced by the key name in config.js
  'angular',
  'ng-loading-bar',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  'tooltip',
  'rzModule',
  './modules/common/rpc-service',
  './modules/common/project-service',
  './modules/common/poller-service',
  './modules/common/icon-directive',
  './modules/common/form-input-validate-directive',
  './modules/common/local-storage-polyfill',
  './modules/charts/charts',
  './modules/optimization/optimization',
  './modules/scenarios/scenarios',
  './modules/admin/users',
  './modules/admin/projects',
  './modules/calibration/calibration',
  './modules/project/create-project',
  './modules/project/projects',
  './modules/geospatial/geospatial',
  './modules/costfunction/costfunction',
  './modules/programs/programs',
  './modules/user/user',
  './modules/user/user-manager-service',
  './modules/ui/modal-service',
  './modules/ui/main-ctrl',
  './modules/ui/menu-directive',
  './modules/ui/modal-service',
], function (angular) {

  'use strict';

  return angular
    .module('app',
      [
        // the actual loading into app occurs here by
        // reference to the name of the module assigned
        // by the require.js/angular module system.
        // these names are defined in the respective
        // module definition system

        // these are the third-party plug-ins
        'angularFileUpload', // for $upload service
        'angular-loading-bar',
        'ui.bootstrap', // for $modal services
        'ui.router', // to create $stateProviders defining url
        'tooltip.module', // tooltips
        'rzModule', // sliders for the graphs

        // these are services available to other modules
        'app.local-storage', // to save user's active project between sessions
        'app.rpc-service', // to provide direct calls to the web-server
        'app.form-input-validate',
        'app.project-service', // global variable for projects, calls to web-server
        'app.poller-service', // to poll for async tasks on server
        'app.icon-directive', // create elements for icons
        'app.modal', // custom modals based on $modal of ui.bootstrap modals
        'app.user', // controllers and pages for edit/help/feedback/home/register/login
        'app.user-manager', // legacy api callers to the website for user calls
        'app.charts', // elements to display charts and chart controls

        // these controllers are for the base-page
        'app.main', // controller for user/project in top-right corner
        'app.menu', // controller for menu options

        // the following correspond to pages from the site
        'app.create-project',
        'app.admin-projects',
        'app.admin-users',
        'app.project',
        'app.calibration',
        'app.programs',
        'app.cost-functions',
        'app.scenarios',
        'app.optimization',
        'app.geospatial',
      ])

    .config(function ($httpProvider) {
      $httpProvider.interceptors.push(function ($q, $injector) {
        return {
          responseError: function (rejection) {
            if (rejection.status === 401 && rejection.config.url !== '/api/users/current') {
              // this is where login errors are intercepted
              // Redirect them back to login page
              location.href = './#/login';

              return $q.reject(rejection);
            } else {
              // this is where errors from the webservers are
              // parsed for the python track trace, which
              // is stored in a data.message | data.reason property
              var message, errorText;
              console.log('catching error', rejection);

              isJsonBlob = function(data) { // Used for the rpcDownload which has responseType: 'blob'
                return data instanceof Blob && data.type === "application/json";
              }

              errorText = null;
              getRejectionMessagePromise = function(rejection) {
                return new Promise(function (resolve, reject) {
                  if (rejection.data && (rejection.data.message || rejection.data.exception || rejection.data.reason)) {
                    errorText = rejection.data.message || rejection.data.exception || rejection.data.reason;
                  } else if (isJsonBlob(rejection.data)) { // Used for the rpcDownload which has responseType: 'blob'
                      const responseData = isJsonBlob(rejection.data) ? (rejection.data).text() : rejection.data || {};
                      const responseJson = (typeof responseData === "string") ? JSON.parse(responseData) : responseData;
                      responseJson.then(function(response) {  // responseJson is a Promise object so we convert
                        const insideJson = (typeof response === "string") ? JSON.parse(response) : response;
                        resolve(insideJson.exception);
                      });
                      resolve(responseJson);
                  } else {
                    errorText = 'Unknown error, check Internet connection and try again.\n' + JSON.stringify(rejection, null, 2);
                  }
                  resolve(errorText);

                });
              }

              getRejectionMessagePromise(rejection)
              .then(function(response) {
                console.log('inside', response, errorText)
                message = 'We are very sorry, but it seems an error has occurred. Please contact us (info@optimamodel.com). In your email, copy and paste the error message below, and please also provide the date and time, your user name, the project you were working on (if applicable), and as much detail as possible about the steps leading up to the error. We apologize for the inconvenience.';
                var modalService = $injector.get('modalService');
                modalService.inform(angular.noop, 'Okay', message, 'Server Error', errorText);
              })

              return $q.reject(rejection);
            }
          }
        };
      });
    })

    .config(function ($urlRouterProvider) {
      $urlRouterProvider.otherwise('/');
    })

    .run(function ($rootScope, $state, userManager, projectService) {

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
      projectService.loadActiveProject();

      function isStatePublic(stateName) {
        var publicStates = ['contact', 'login', 'register', 'devregister'];
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
