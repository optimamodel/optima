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
          getParameters: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'parameters',
              suffix: 'data'
            }
          },
          getParametersF: {
            method: 'GET',
            isArray: true,
            params: {
              path: 'parameters',
              suffix: 'F'
            }
          },
          getParametersG: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'parameters',
              suffix: 'G'
            }
          },
          getParametersData: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'parameters',
              suffix: 'data'
            }
          },
          getParametersDataMeta: {
            method: 'GET',
            isArray: false,
            params: {
              path: 'parameters',
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
              path: 'parameters',
              suffix: 'programs'
            }
          }
        }
      );
    });
});
