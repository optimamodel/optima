define(
  ['angular', 'ui.router', '../project/project-api-service', '../charts/export-all-charts-directive'],
  function (angular) {

    'use strict';

    return angular
      .module('app.geospatial', ['app.export-all-charts', 'ui.router'])
      .config(function ($stateProvider) {
        $stateProvider
          .state('portfolio', {
            url: '/portfolio',
            abstract: true,
            template: '<div ui-view=""></div>'
          })
          .state('portfolio.manage', {
            url: '/portfolio',
            templateUrl: 'js/modules/geospatial/manage-portfolio.html',
            controller: 'PortfolioController',
          })
      });

  });
