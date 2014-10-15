define([
  'angular',
  'ui.router',
  '../resources/data-mocks',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.model', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('model.view', {
          url: '/view',
          templateUrl: 'js/modules/model/view.html',
          controller: 'GraphsController'
        })
        .state('model.automatic-calibration', {
          url: '/automatic-calibration',
          templateUrl: 'js/modules/model/automatic-calibration.html',
          controller: 'GraphsController'
        })
        .state('model.manual-calibration', {
          url: '/manual-calibration',
          templateUrl: 'js/modules/model/manual-calibration.html',
          controller: 'GraphsController'
        });
    });

});
