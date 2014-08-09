/**
 * loads sub modules and wraps them up into the main module.
 * This should be used for top-level module definitions only.
 */
define([
  'angular',
  'n3-line-chart',
  'ui.router',
  './config',
  './modules/analyses/index',
  './modules/common/save-graph-as-directive',
  './modules/graphs/index',
  './modules/home/index',
  './modules/playground/index',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
    'app.constants',
    'app.analyses',
    'app.graphs',
    'app.home',
    'app.playground',
    'app.save-graph-as',
    'app.ui',
    'n3-line-chart',
    'ui.router'
  ]).config(['$urlRouterProvider', function ($urlRouterProvider) {
    $urlRouterProvider.otherwise('/');
  }]);

});
