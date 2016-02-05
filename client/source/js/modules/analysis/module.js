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

  return angular.module('app.analysis', [
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
                  scenarioParametersResponse: function($http, info) {
                    //return $http.get('/api/analysis/scenarios/list');
                  },
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
                templateUrl: 'js/modules/analysis/optimization.html' ,
                controller: 'AnalysisOptimizationController',
                resolve: {
                  optimizations: function($http) {
                    return $http.get('/api/analysis/optimization/list');
                  }
                }
            });
    });

});
