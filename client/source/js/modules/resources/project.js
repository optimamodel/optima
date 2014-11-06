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
          getCurrent: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'name'
            }
          },
          list: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'list'
            }
          }
        }
      );
    });
});
