define([
  'angular',
  'ui.router',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.graphs', [
    'app.constants',
    'ui.router'
  ]).config(function ($stateProvider) {
    $stateProvider
      .state('graphs', {
        url: '/graphs',
        templateUrl: 'js/modules/graphs/graphs.html' ,
        controller: 'GraphsController',
        resolve: {
          mocks: function ($http) {
            return $http.get('/assets/mocks/graphs.json');
          }
        }
      });
  });

});
