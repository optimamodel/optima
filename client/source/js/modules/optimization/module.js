define(['angular', 'ui.router'], function (angular) {
    'use strict';

    return angular.module('app.optimization', ['ui.router'])
        .config(function ($stateProvider) {
            $stateProvider
                .state('optimization', {
                    url: '/optimization',
                    abstract: true,
                    template: '<div ui-view=""></div>'
                })
                .state('optimization.objectives', {
                    url: '/objectives',
                    templateUrl: 'js/modules/optimization/objectives.html',
                    controller: 'OptimizationObjectivesController'
                })
                .state('optimization.constraints', {
                    url: '/constraints',
                    templateUrl: 'js/modules/optimization/constraints.html',
                    controller: 'OptimizationConstraintsController'
                })
                .state('optimization.optimize', {
                    url: '/optimize',
                    templateUrl: 'js/modules/optimization/optimize.html',
                    controller: 'OptimizationOptimizeController'
                });
        });

});
