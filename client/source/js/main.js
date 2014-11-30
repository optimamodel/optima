/**
 * Bootstraps angular onto the window.document node.
 * NOTE: the ng-app attribute should not be on the index.html when using ng.bootstrap
 */
define([
  'angular',
  './app'
], function (angular) {
  'use strict';

  // You can place operations that need to initialize prior to app start here
  // using the `run` function on the top-level module
  angular.injector([
    'ng',
    'app.active-project',
    'app.resources.user'
  ])
    .invoke([
      'activeProject', 'User',
      function (activeProject, User) {

        var bootstrap = function () {
          angular.bootstrap(document, ['app']);
        };

        User.getCurrent(function (user) {
          window.user = user;
        }).$promise.then(bootstrap, bootstrap);

      }]);
});
