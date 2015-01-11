define([
  'angular',
  'ui.router',
  '../resources/model',
  '../resources/project',
  '../ui/type-selector/index',
  '../common/graph-type-factory'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.resources.model',
    'app.resources.project',
    'app.ui.type-selector',
    'ui.router',
    'app.common.graph-type'
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
            f: function (Model) {
              return Model.getParametersF().$promise;
            },
            G: function (Model) {
              return Model.getParametersG().$promise;
            },
            meta: function (Model) {
              return Model.getParametersDataMeta().$promise;
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
              return Model.getParametersDataMeta().$promise;
            }
          }
        });
    });

});
