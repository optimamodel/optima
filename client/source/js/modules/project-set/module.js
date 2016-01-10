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

  return angular.module('app.project-set', [
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
        .state('project-set', {
          url: '/project-set',
          abstract: true,
          template: '<div ui-view></div>',
          resolve: {
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
        .state('project-set.manageProgramSet', {
          url: '/programs',
          templateUrl: 'js/modules/project-set/program-set/program-set.html',
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
        .state('project-set.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController',
          templateUrl: 'js/modules/project-set/cost-coverage.html',
          resolve: {
            programsResource: function(Model) {
              return Model.getPrograms().$promise;
            }
          }
        });
    });
});
