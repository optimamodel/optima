define([
  'angular',
  'n3-line-chart',
  'ui.router',
  './config',
  './modules/analyses/index',
  './modules/graphs/index',
  './modules/home/index',
  './modules/import-export/index',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
    'app.constants',
    'app.analyses',
    'app.graphs',
    'app.home',
    'app.import-export',
    'app.ui',
    'n3-line-chart',
    'ui.router'
  ]).config(['$urlRouterProvider', function ($urlRouterProvider) {
    $urlRouterProvider.otherwise('/');
  }]);

});
