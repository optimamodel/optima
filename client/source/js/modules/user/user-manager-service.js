define(['angular', './user-api-service' ], function (angular) {
  'use strict';

  return angular
    .module('app.user-manager', ['app.user-api'])
    .service('userManager', function() {
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
