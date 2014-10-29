define(['angular', 'ui.router'], function (angular) {
    'use strict';

    return angular.module('app.forecasts', ['ui.router'])
        .config(function ($stateProvider) {
            $stateProvider
                .state('forecasts', {
                    url: '/forecasts',
                    abstract: true,
                    template: '<div ui-view=""></div>'
                })
                .state('forecasts.counterfactuals', {
                    url: '/counterfactuals',
                    templateUrl: 'js/modules/forecasts/counterfactuals.html',
                    controller: 'ForecastsCounterfactualsController'
                })
                .state('forecasts.results', {
                    url: '/results',
                    templateUrl: 'js/modules/forecasts/results.html',
                    controller: 'ForecastsResultsController'
                });
        });

});
