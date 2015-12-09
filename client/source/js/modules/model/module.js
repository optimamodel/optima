define([
  'angular',
  'ui.router',
  '../resources/model',
  '../resources/project',
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
    'app.resources.project',
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
            info: function(Project) {
              return Project.info().$promise;
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
        .state('model.manageResponses', {
          url: '/programs',
          templateUrl: 'js/modules/model/project-set/project-set.html',
          controller: 'ProjectSetController'
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
