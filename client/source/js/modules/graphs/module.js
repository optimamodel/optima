define([
  'angular',
  'ui.router',
  '../resources/data-mocks',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.graphs', [
    'app.constants',
    'app.resources.data-mocks',
    'ui.router'
  ]).config(function ($stateProvider) {
    $stateProvider
      .state('graphs', {
        url: '/graphs',
        templateUrl: 'js/modules/graphs/graphs.html' ,
        controller: 'GraphsController'
      });
  });

});
