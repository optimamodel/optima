define(['angular', 'ng-resource'], function (angular) {

  /**
   * userApi is a legacy injectable module that provides
   * an abstracted way to call the web-server for user
   * related functions - verifying user logins and
   * getting current user
   */

  angular
    .module('app.user-api', ['ngResource'])
    .service('userApi', function ($resource) {
      return $resource('/api/user/:path',
        { path: '@path' },
        {
          getCurrent: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'current'
            }
          },
          create: {
            method: 'POST',
            isArray: false,
            params: {
              path: ''
            }
          },
          update: {
            method: 'PUT',
            isArray: false,
            params: {
              path: '@id'
            }
          },
          login: {
            method: 'POST',
            isArray: false,
            params: {
              path: 'login'
            }
          }
        }
      );
    });
});
