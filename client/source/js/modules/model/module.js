define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../resources/model',
  '../ui/type-selector/index',
  '../common/export-all-charts',
  '../common/export-all-data',
  '../validations/more-than-directive',
  '../validations/less-than-directive'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'app.ui.type-selector',
    'ui.router',
    'app.validations.more-than',
    'app.validations.less-than'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('model.manual', {
          url: '/manual',
          templateUrl: 'js/modules/model/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            parameters: function (Model) {
              //return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              // return Model.getKeyDataMeta().$promise;
            },
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
        .state('model.auto', {
          url: '/auto',
          templateUrl: 'js/modules/model/auto/auto-calibration.html',
          controller: 'ModelAutoCalibrationController',
          resolve: {
            parameters: function (Model) {
              //return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              // return Model.getKeyDataMeta().$promise;
            },
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
    });
});
