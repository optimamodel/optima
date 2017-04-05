define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../analysis/parameter-scenarios-modal',
  '../analysis/program-scenarios-modal',
], function (angular) {
  'use strict';

  return angular.module(
    'app.analysis',
    [
      'ui.router',
      'app.parameter-scenarios-modal',
      'app.program-scenarios-modal',
    ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('analysis', {
          url: '/analysis',
          abstract: true,
          template: '<div ui-view></div>',
        })
        .state('analysis.scenarios', {
          url: '/scenarios',
          templateUrl: 'js/modules/analysis/scenarios.html' ,
          controller: 'AnalysisScenariosController',
        })
        .state('analysis.optimization', {
          url: '/optimization',
          templateUrl: 'js/modules/analysis/optimization.html',
          controller: 'AnalysisOptimizationController',
        });
    });

});
