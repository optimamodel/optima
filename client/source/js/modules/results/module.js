define(['angular', 'ui.router'], function (angular) {
    'use strict';

    return angular.module('app.results', ['ui.router'])
        .config(function ($stateProvider) {
            $stateProvider
                .state('results', {
                    url: '/results',
                    abstract: true,
                    template: '<div ui-view=""></div>'
                })
                .state('results.results', {
                    url: '/results',
                    templateUrl: 'js/modules/results/results.html',
                    controller: 'ViewResultsController'
                })
        });

});
