define([
  'angular',
  'ui.router',
  'toastr',
  '../project/project-api-service',
  '../resources/model',
  '../ui/type-selector/index',
  '../common/export-all-charts',
  '../common/export-all-data',
  '../validations/more-than-directive',
  '../validations/less-than-directive',
  '../validations/year-directive'
], function (angular) {
  'use strict';

  return angular.module('app.project-set', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'app.ui.type-selector',
    'ui.router',
    'app.validations.more-than',
    'app.validations.less-than',
    'app.validations.year',
    'toastr'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('project-set', {
          url: '/project-set',
          abstract: true,
          template: '<div ui-view></div>'
        })
        .state('project-set.manageProgramSet', {
          url: '/programs',
          templateUrl: 'js/modules/project-set/program-set/program-set.html',
          controller: 'ProgramSetController',
          resolve: {
            currentProject: function(projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
        .state('project-set.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController as vm',
          templateUrl: 'js/modules/project-set/cost-coverage/cost-coverage.html',
          bindToController: true,
          resolve: {
            activeProject: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        });
    });
});
