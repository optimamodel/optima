define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval,
    Model, parameters, meta, info, CONFIG, typeSelector, cfpLoadingBar, calibration, modalService) {

    var activeProjectInfo = info.data;

    if (!activeProjectInfo.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $scope.missingData = true;
      return;
    }

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
      $http.get('/api/parset/' + $scope.selectedParset.id + '/calibration').
      success(function (response) {
        $scope.calibrationChart = response.calibration.graphs;
      });
    }

  });
});
