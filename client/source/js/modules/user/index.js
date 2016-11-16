define(['angular', './user-api-service' ], function (angular) {
  'use strict';

  return angular
    .module('app.user-manager', ['app.user-api'])
    .service('UserManager', function() {
      var userManager = {
        isLoggedIn: false,
        isAdmin: false,
        currentUser: {},
        setUser: function (user) {
          userManager.isLoggedIn = true;
          userManager.isAdmin = user.is_admin;
          angular.extend(userManager.currentUser, user);
        }
      };
      return userManager;
    });

});
