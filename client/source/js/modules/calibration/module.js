define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../charts/export-all-charts-directive',
], function (angular) {
  'use strict';

  return angular.module('app.model', ['app.export-all-charts', 'ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('model.manual', {
          url: '/manual',
          templateUrl: 'js/modules/calibration/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
    });
});
