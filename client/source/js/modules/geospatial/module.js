define(
  ['angular', 'ui.router', '../project/project-api-service'],
  function (angular) {

    'use strict';

    return angular
      .module('app.geospatial', ['ui.router'])
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
