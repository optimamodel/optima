define([
  'angular',
  'ui.router',
  '../resources/model',
  '../ui/type-selector/index'
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.resources.model',
    'app.ui.type-selector',
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
          templateUrl: 'js/modules/model/view-calibration.html',
          controller: 'ModelViewController',
          resolve: {
            //data: function (Model) {
            //  return Model.getParametersData();
            //},
            info: function($http) {
              return $http.get('/api/project/info');
            },
            f: function (Model) {
              return Model.getParametersF().$promise;
            },
            meta: function (Model) {
              return Model.getParametersDataMeta().$promise;
            }
          }
        })
        .state('model.define-cost-coverage-outcome', {
          url: '/define-cost-coverage-outcome',
          controller: 'ModelViewCalibrationController',
          templateUrl: 'js/modules/model/define-cost-coverage-outcome.html',
          resolve: {
            meta: function (Model) {
              return Model.getParametersDataMeta().$promise;
            }
          }
        });
    });

});
