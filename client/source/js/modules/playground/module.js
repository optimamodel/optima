define([
  'angular',
  'ui.router',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.playground', [
      'app.constants',
      'ui.router'
    ]).config(function ($stateProvider) {
    $stateProvider
      .state('playground', {
        url: '/playground',
        templateUrl: 'js/modules/playground/playground.html',
        controller: 'PlaygroundController'
      });
  });

});
