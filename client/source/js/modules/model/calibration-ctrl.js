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
          $http.get('/api/parset/' + $scope.selectedParset.id + '/calibration').
          success(function (response) {
            setCalibrationData(response.calibration);
          });
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
      $http.put('/api/parset/' + $scope.selectedParset.id + '/calibration', data).
      success(function (response) {
        setCalibrationData(response.calibration);
      });
    };

    var setCalibrationData = function(calibration) {
      $scope.calibrationChart = calibration.graphs;
      $scope.selectors = calibration.selectors;
      defaultParameters = calibration.parameters;
      $scope.parameters = copy(response.calibration.parameters);
    };

    $scope.resetParameters = function() {
      $scope.parameters = angular.copy(defaultParameters);
    }

  });
});
