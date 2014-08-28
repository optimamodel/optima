define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.results', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('results', {
          url: '/results',
          templateUrl: 'js/modules/results/results.html',
          controller: 'ResultsController'
        });
    })
    .controller('ResultsController', function () {});

});
