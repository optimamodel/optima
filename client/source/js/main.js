define(['angular', './app'], function(angular) {

  'use strict';

  angular
    .injector(['ng', 'app.user-api'])
    .invoke(['UserApi', function(UserApi) {
      /**
       * Bootstraps angular onto the window.document node.
       * You can place operations that need to initialize prior
       * to app.run(). Data must be stored in the global window,
       * as modules haven't been instantiated yet
       *
       * NOTE: the ng-app attribute should not be on the
       * index.html when using ng.bootstrap
       */
      function bootstrap() {
        angular.bootstrap(document, ['app']);
      }

      UserApi
        .getCurrent(function(user) {
          window.user = user;
        })
        .$promise.then(bootstrap, bootstrap);

    }]);

});
