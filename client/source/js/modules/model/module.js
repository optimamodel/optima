define([
  'angular',
  'ui.router',
  '../resources/model',
  '../resources/project',
  '../ui/type-selector/index',
  '../common/export-all-charts',
  '../common/export-all-data',
  '../common/graph-type-factory',
  '../validations/error-messages-directive',
  '../validations/error-custom-messages-directive',
  '../validations/ng-min-directive',
  '../validations/ng-max-directive',
  '../validations/more-than-directive',
  '../validations/less-than-directive'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'app.resources.project',
    'app.ui.type-selector',
    'ui.router',
    'app.common.graph-type',
    'app.validations.error-messages',
    'app.validations.error-custom-messages',
    'app.validations.ng-min',
    'app.validations.ng-max',
    'app.validations.more-than',
    'app.validations.less-than'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view></div>'
        })
        .state('model.view', {
          url: '/view',
          templateUrl: 'js/modules/model/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            info: function(Project) {
              return Project.info().$promise;
            },
            parameters: function (Model) {
              return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              return Model.getKeyDataMeta().$promise;
            }
          }
        })
        .state('model.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController',
          templateUrl: 'js/modules/model/cost-coverage.html',
          resolve: {
            info: function(Project) {
              return Project.info().$promise;
            },
            meta: function (Model) {
              return Model.getKeyDataMeta().$promise;
            },
            programs: function(Model) {
              return Model.getPrograms().$promise;
            }
          }
        });
    });
});
