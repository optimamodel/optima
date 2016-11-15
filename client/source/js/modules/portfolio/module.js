define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../resources/model',
  '../charts/export-all-charts',
], function (angular) {
  'use strict';

  return angular.module('app.portfolio', [
    'app.export-all-charts',
    'app.resources.model',
    'ui.router',
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('portfolio', {
          url: '/portfolio',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('portfolio.manage', {
          url: '/portfolio',
          templateUrl: 'js/modules/portfolio/manage-portfolio.html',
          controller: 'PortfolioController',
        })
    });
});
