define(['angular', './app' ], function (angular) {

    'use strict';

    /**
     * Bootstraps angular onto the window.document node.
     * NOTE: the ng-app attribute should not be on the index.html when using ng.bootstrap
     *
     * You can place operations that need to initialize prior to app start here
     * using the `run` function on the top-level module
     */

    angular
        .injector(['ng', 'app.user-api'])
        .invoke(['UserApi', function (UserApi) {
            var bootstrap = function () { angular.bootstrap(document, ['app']); };

            UserApi.getCurrent(
              function(user) {
                 // no-no flag, we should be using the UserManager here, not a global
                 window.user = user;
              })
              .$promise.then(bootstrap, bootstrap);
        }]);

});
