define([
  'angular',
  'angular-nvd3',
  'ng-file-upload',
  'ui.bootstrap',
  'ui.router',
  './config',
  './modules/about/index',
  './modules/analyses/index',
  './modules/common/save-graph-as-directive',
  './modules/common/line-scatter-area-directive',
  './modules/common/line-scatter-directive',
  './modules/graphs/index',
  './modules/help/index',
  './modules/home/index',
  './modules/model/index',
  './modules/optimization/index',
  './modules/playground/index',
  './modules/project/index',
  './modules/import-export/index',
  './modules/results/index',
  './modules/ui/index'
], function (angular) {
  'use strict';

  return angular.module('app', [
    'angularFileUpload',
    'app.about',
    'app.constants',
    'app.analyses',
    'app.graphs',
    'app.help',
    'app.home',
    'app.import-export',
    'app.line-scatter-chart',
    'app.line-scatter-area-chart',
    'app.model',
    'app.optimization',
    'app.playground',
    'app.project',
    'app.results',
    'app.save-graph-as',
    'app.ui',
    'nvd3',
    'ui.bootstrap',
    'ui.router'
  ]).config(function ($urlRouterProvider) {
    $urlRouterProvider.otherwise('/');
  });

});
