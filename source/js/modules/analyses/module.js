define([
  'angular',
  'ui.router',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.analyses', [
    'app.constants',
    'ui.router'
  ]).config(['$stateProvider', function ($stateProvider) {
    $stateProvider
      .state('analyses', {
        url: '/analyses',
        templateUrl: 'js/modules/analyses/analyses.html' ,
        controller: 'AnalysesController'
      })
  }]);

});
