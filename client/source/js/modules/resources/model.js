define([
  'angular',
  'angular-resource'
], function (angular) {

  angular.module('app.resources.model', [
    'ngResource'
  ])
    .service('Model', function ($resource) {
      return $resource('/api/model/:path/:suffix/:postsuffix',
        { path: '@path' },
        {
          saveCalibrateManual: {
            method: 'POST',
            isArray: false,
            params: {
              path: 'calibrate',
              suffix: 'manual'
            }
          },
          getKeyData: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'data',
              suffix: 'data'
            }
          },
          getKeyF: {
            method: 'GET',
            isArray: true,
            params: {
              path: 'data',
              suffix: 'F'
            }
          },
          getKeyG: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'data',
              suffix: 'G'
            }
          },
          getKeyDataMeta: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'data',
              suffix: 'data',
              postsuffix: 'meta'
            }
          },
          getCalibrateParameters: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'calibrate',
              suffix: 'parameters'
            }
          },
          getPrograms: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'data',
              suffix: 'programs'
            }
          }
        }
      );
    });
});
