define([
  'angular',
  'underscore',
  '../resources/user'
], function (angular, _) {
  'use strict';

  return angular.module('app.user-manager', ['app.resources.user'])

    .service('UserManager', function ($window, User, localStorage) {
      var user_manager = {
        isLoggedIn: false,
        isAdmin: false,
        data: new User(),
        set: function (data) {
          user_manager.isLoggedIn = true;
          user_manager.isAdmin = data.is_admin;
          angular.extend(user_manager.data, data);
        }
      };
      return user_manager;
    });
});
