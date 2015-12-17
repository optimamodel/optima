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
          template: '<div ui-view></div>',
          resolve: {
            info: function (projectApiService) {
              projectApiService.getActiveProject();
            }
          }
        })
        .state('model.view', {
          url: '/view',
          templateUrl: 'js/modules/model/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            parameters: function (Model) {
              return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              return Model.getKeyDataMeta().$promise;
            }
          }
        })
        .state('model.manageProgramSet', {
          url: '/programs',
          templateUrl: 'js/modules/model/program-set/program-set.html',
          controller: 'ProgramSetController',
          resolve: {
            availableParameters: function(projectApiService) {
              return projectApiService.getParameters();
            },
            predefined: function(projectApiService) {
              return projectApiService.getPredefined();
            }
          }
        })
        .state('model.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController',
          templateUrl: 'js/modules/model/cost-coverage.html',
          resolve: {
            programsResource: function(Model) {
              return Model.getPrograms().$promise;
            }
          }
        });
    });
});
