define(['angular', './app'], function(angular) {

  'use strict';

  /**
   * Bootstraps angular onto the window.document node.
   * You can place operations that need to initialize prior
   * to app.run(). Data must be stored in the global window,
   * as modules haven't been instantiated yet
   *
   * NOTE: the ng-app attribute should not be on the
   * index.html when using ng.bootstrap
   */

  angular
    .injector(['ng', 'app.user-api'])
    .invoke(['userApi', function(userApi) {

      function bootstrap() {
        angular.bootstrap(document, ['app']);
      }

      // the only way to pass the user into the app
      // before the app is initialized is via a global
      // attached to the window context window.user
      // after window.user, bootstrap is called
      userApi
        .getCurrent(function(user) { window.user = user; })
        .$promise.then(bootstrap, bootstrap);

    }]);

});
