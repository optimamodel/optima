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
        .state('results.epiresults', {
          url: '/epiresults',
          templateUrl: 'js/modules/results/epiresults.html',
          controller: 'ResultsEpiresultsController'
        })
        .state('results.econresults', {
          url: '/econresults',
          templateUrl: 'js/modules/results/econresults.html',
          controller: 'ResultsEconresultsController'
        });
    });

});
