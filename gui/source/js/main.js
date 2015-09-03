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
    'app.resources.user'
  ])
    .invoke(['User', function (User) {
        var bootstrap = function () {
          angular.bootstrap(document, ['app']);
        };

        User.getCurrent(function (user) {
          window.user = user;  // no-no flag, we should be using the UserManager here, not a global
        }).$promise.then(bootstrap, bootstrap);

      }]);
});
