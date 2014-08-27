define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.model', ['ui.router'])
    .config(['$stateProvider', function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('model.view', {
          url: '/create',
          templateUrl: 'js/modules/model/view.html',
          controller: 'ModelViewController'
        })
        .state('model.automatic-calibration', {
          url: '/automatic-calibration',
          templateUrl: 'js/modules/model/automatic-calibration.html',
          controller: 'ModelAutomaticCalibrationController'
        })
        .state('model.manual-calibration', {
          url: '/manual-calibration',
          templateUrl: 'js/modules/model/manual-calibration.html',
          controller: 'ModelManualCalibrationController'
        });
    }]);

});
