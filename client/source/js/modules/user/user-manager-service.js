define(['angular', './user-api-service' ], function (angular) {
  'use strict';

  return angular
    .module('app.user-manager', ['app.user-api'])
    .service('userManager', function() {

      /**
       * UserManager provides a global variable for
       * the current user in the web-client
       *
       * At login or initialization, userManager.setUser is
       * called, setting userManager.user to the current
       * user. This is used in the app to query the
       * user.
       */
      var userManager = {
        isLoggedIn: false,
        isAdmin: false,
        user: {},
        setUser: function (user) {
          userManager.isLoggedIn = true;
          userManager.isAdmin = user.is_admin;
          angular.extend(userManager.user, user);
        }
      };
      return userManager;
    });

});
