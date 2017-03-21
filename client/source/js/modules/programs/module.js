define([
  'angular',
  'ui.router',
  'toastr',
  '../project/project-api-service',
  ], function (angular) {
  'use strict';

  return angular.module('app.programs', [
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
            currentProject: function(projectApi) {
              return projectApi.getActiveProject();
            }
          }
        })
        .state('programs.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelCostCoverageController as vm',
          templateUrl: 'js/modules/programs/cost-coverage/cost-coverage.html',
          bindToController: true,
          resolve: {
            activeProject: function (projectApi) {
              return projectApi.getActiveProject();
            }
          }
        });
    });
});
