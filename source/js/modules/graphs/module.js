define([
  'angular',
  'ui.router',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.graphs', [
    'app.constants',
    'ui.router'
  ]).config(['$stateProvider', function ($stateProvider) {
    $stateProvider
      .state('graphs', {
        url: '/graphs',
        templateUrl: 'js/modules/graphs/graphs.html' ,
        controller: 'GraphsController'
      })
  }]);

});
