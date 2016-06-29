define([
  'angular',
  'ui.router',
  'toastr',
  '../project/project-api-service',
  '../resources/model',
  '../ui/type-selector/index',
  '../mpld3-charts/export-all-charts',
  '../mpld3-charts/export-all-data',
  '../validations/more-than-directive',
  '../validations/less-than-directive',
  '../validations/year-directive',
  '../validations/range-limit',
], function (angular) {
  'use strict';

  return angular.module('app.programs', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'app.ui.type-selector',
    'ui.router',
    'app.validations.more-than',
    'app.validations.less-than',
    'app.validations.year',
    'app.validations.range-limit',
    'toastr'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('programs', {
          url: '/programs',
          abstract: true,
          template: '<div ui-view></div>'
        })
        .state('programs.manageProgramSet', {
          url: '/programs',
          templateUrl: 'js/modules/programs/program-set/program-set.html',
          controller: 'ProgramSetController',
          resolve: {
            currentProject: function(projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
        .state('programs.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController as vm',
          templateUrl: 'js/modules/programs/cost-coverage/cost-coverage.html',
          bindToController: true,
          resolve: {
            activeProject: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        });
    });
});
