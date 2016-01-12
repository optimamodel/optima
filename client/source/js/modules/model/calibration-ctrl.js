define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval,
    Model, parameters, meta, info, CONFIG, typeSelector, cfpLoadingBar, calibration, modalService) {

    var activeProjectInfo = info.data;
    var defaultParameters;

    $scope.parsets = [];
    $scope.selectedParset = undefined;

    $http.get('/api/project/' + activeProjectInfo.id + '/parsets').
      success(function (response) {
        var parsets = response.parsets;
        if(parsets) {
          $scope.parsets = parsets;
          $scope.selectedParset = parsets[0];
          $scope.displayGraphs();
        }
      });

    $scope.displayGraphs = function() {
      var data = {};
      if($scope.parameters) {
        data.parameters = $scope.parameters;
      }
      if($scope.selectors) {
        var selectors = _.filter($scope.selectors, function(selector) {
          return selector.checked;
        }).map(function(selector) {
          return selector.key;
        });
        if(selectors && selectors.length > 0) {
          data.which = selectors;
        }
      }

      //$http.put('/api/parset/' + $scope.selectedParset.id + '/calibration', data).

      $http.get('/api/parset/' + $scope.selectedParset.id + '/calibration').
      success(function (response) {
        $scope.calibrationChart = response.calibration.graphs;
        $scope.selectors = response.calibration.selectors;
        defaultParameters = response.calibration.parameters;
        $scope.parameters = angular.copy(response.calibration.parameters);
      });
    };

    $scope.resetParameters = function() {
      $scope.parameters = angular.copy(defaultParameters);
    }

  });
});
