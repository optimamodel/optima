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
        clean: function () {
          user_manager.isLoggedIn = false;
debugger
          // Reset state about the active project
          localStorage.removeItem('project');

          // Safely clean User object
          _(_(user_manager.data).keys()).each(function (key) {
            user_manager.data[key] = null;
          });
        },
        data: new User(),
        set: function (data) {
          user_manager.isLoggedIn = true;
          angular.extend(user_manager.data, data);
        },
        logout: function () {
          User.logout(function () {
            user_manager.clean();
            $window.location = '/#/login';
          });
        }
      };

      return user_manager;
    });
});
