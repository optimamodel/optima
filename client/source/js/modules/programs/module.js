define([
  'angular',
  'ui.router',
  'toastr',
  '../project/project-api-service',
  '../charts/export-all-charts-directive',
  ], function (angular) {
  'use strict';

  return angular.module('app.programs', [
    'app.export-all-charts',
    'ui.router',
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
