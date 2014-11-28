define([
    'angular',
    'ui.router',
    '../../config',
    '../resources/model'
], function (angular) {
    'use strict';

    return angular.module('app.analysis', [
        'app.constants',
        'app.resources.model',
        'ui.router'
    ]).config(function ($stateProvider) {
        $stateProvider
            .state('analysis', {
                url: '/analysis',
                abstract: true,
                template: '<div ui-view></div>'
            })
            .state('analysis.scenarios', {
                url: '/scenarios',
                templateUrl: 'js/modules/analysis/scenarios.html' ,
                controller: 'AnalysisScenariosController',
                resolve: {
                  meta: function (Model) {
                    return Model.getParametersDataMeta().$promise;
                  },
                  scenarioParamsResponse: function($http) {
                    return $http.get('/api/analysis/scenarios/params');
                  }
                }
            })
            .state('analysis.optimization', {
                url: '/optimization',
                templateUrl: 'js/modules/analysis/optimization.html' ,
                controller: 'AnalysisOptimizationController'
            });
    });

});
