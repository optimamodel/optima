define([
  'angular',
  'angular-resource'
], function (angular) {

  angular.module('app.resources.project', [
    'ngResource'
  ])
    .service('Project', function ($resource) {
      return $resource('/api/project/:path',
        { path: '@path' },
        {
          list: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'list'
            }
          },
          info: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'info'
            }
          }
        }
      );
    });
});
