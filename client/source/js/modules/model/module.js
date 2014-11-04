define([
  'angular',
  'ui.router'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'ui.router'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view></div>'
        })
        .state('model.view', {
          url: '/view',
          templateUrl: 'js/modules/model/view-calibration.html'
        })
        .state('model.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          templateUrl: 'js/modules/model/define-cost-coverage-outcome.html'
        });
    });

});
