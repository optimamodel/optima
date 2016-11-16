define(['angular', 'ng-resource'], function (angular) {
  angular
    .module('app.user-api', ['ngResource'])
    .service('UserApi', function ($resource) {
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
