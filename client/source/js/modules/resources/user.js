define([
  'angular',
  'angular-resource'
], function (angular) {

  angular.module('app.resources.user', [
    'ngResource'
  ])
    .service('User', function ($resource) {
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
