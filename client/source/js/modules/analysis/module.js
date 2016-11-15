define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../resources/model',
  '../charts/export-all-charts',
  '../charts/export-all-data',
  '../analysis/parameter-scenarios-modal',
  '../analysis/program-scenarios-modal',
], function (angular) {
  'use strict';

  return angular.module(
    'app.analysis',
    [
      'app.export-all-charts',
      'app.export-all-data',
      'app.resources.model',
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
          resolve: {
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            },
            meta: function (Model) {
              //return Model.getKeyDataMeta().$promise;
            }
          }
        })
        .state('analysis.scenarios', {
          url: '/scenarios',
          templateUrl: 'js/modules/analysis/scenarios.html' ,
          controller: 'AnalysisScenariosController',
          resolve: {
            scenariosResponse: function($http, info) {
              return $http.get('/api/project/'+info.data.id+'/scenarios');
            },
            progsetsResponse: function($http, info) {
              return $http.get('/api/project/'+info.data.id+'/progsets')
            },
            parsetResponse: function($http, info) {
              return $http.get('/api/project/'+info.data.id+'/parsets')
            }
          }
        })
        .state('analysis.optimization', {
          url: '/optimization',
          templateUrl: 'js/modules/analysis/optimization.html',
          controller: 'AnalysisOptimizationController',
          resolve: {
            activeProject: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        });
    });

});
