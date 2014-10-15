define([
  'angular',
  'angular-resource'
], function (angular) {

  angular.module('app.resources.data-mocks', [
    'ngResource'
  ])
    .service('dataMocks', [
      '$resource',
      function ($resource) {
        return $resource('/api/data/:path',
          {},
          {
            line: {
              method: 'GET',
              isArray: true,
              params: {
                path: 'line'
              }
            },
            stackedArea: {
              method: 'GET',
              isArray: true,
              params: {
                path: 'stacked-area'
              }
            },
            multiBar: {
              method: 'GET',
              isArray: true,
              params: {
                path: 'multi-bar'
              }
            },
            pie: {
              method: 'GET',
              isArray: true,
              params: {
                path: 'pie'
              }
            },
            lineScatterError: {
              method: 'GET',
              params: {
                path: 'line-scatter-error'
              }
            }
          }
        );
      }]);
});
