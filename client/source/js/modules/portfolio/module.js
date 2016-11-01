define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../resources/model',
  '../mpld3-charts/export-all-charts',
  '../mpld3-charts/export-all-data',
  '../validations/more-than-directive',
  '../validations/less-than-directive'
], function (angular) {
  'use strict';

  return angular.module('app.portfolio', [
    'app.export-all-charts',
    'app.export-all-data',
    'app.resources.model',
    'ui.router',
    'app.validations.more-than',
    'app.validations.less-than'
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
