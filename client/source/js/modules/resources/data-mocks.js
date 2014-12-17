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
        return $resource('/api/data/:path/:num',
          {num: '@num'},
          {
            lineScatterError: {
              method: 'GET',
              params: {
                path: 'line-scatter-error'
              }
            },
            lineScatterArea: {
              method: 'GET',
              params: {
                path: 'line-scatter-area'
              }
            }
          }
        );
      }]);
});
