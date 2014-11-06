define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ModelViewController', function ($scope, $http, Model, f, meta) {

    $scope.parameters = {
      types: {
        force: 'Force-of-infection for ',
        init: 'Initial prevalence for ',
        dx: [
          'Testing rate initial value',
          'Testing rate final value',
          'Testing rate midpoint',
          'Testing rate slope'
        ],
        tx1: [
          'First-line ART initial value',
          'First-line ART final value',
          'First-line ART midpoint',
          'First-line ART slope'
        ],
        tx2: [
          'Second-line initial value',
          'Second-line final value',
          'Second-line midpoint',
          'Second-line slope'
        ]
      },
      meta: meta,
      f: f,
      cache: {
        f: angular.copy(f)
      }
    };

    $scope.enableManualCalibration = false;

    $scope.simulationOptions = {};

    $scope.simulate = function () {
      //var generatedDataSet = dataMocks.lineWith({num: $scope.numberOfPoints});
      //$scope.linescatterdata = [generatedDataSet];

      $http.post('/api/model/view', $scope.simulationOptions)
        .success(function (data) {
          console.log(data);
        })
    };

    $scope.openFileOption1 = function () {
      angular.element('#file01').click();
    };

    $scope.scatteroptions = {
      /* CK: need axis labels to align better, and need right number! */
      chart: {
        type: 'scatterChart',
        height: 250,
        margin: {
          top: 20,
          right: 20,
          bottom: 100,
          left: 40
        },
        x: function (d) {
          return d[0];
        },
        y: function (d) {
          return d[1];
        },
        sizeRange: [100, 100],
        clipEdge: true,
        transitionDuration: 500,
        useInteractiveGuideline: true,
        xAxis: {
          showMaxMin: false,
          ticks: 9,
          rotateLabels: -90,
          tickFormat: function (d) {
            return ['Parameter 0', 'Parameter 1', 'Parameter 2', 'Parameter 3', 'Parameter 4', 'Parameter 5', 'Parameter 6', 'Parameter 7', 'Parameter 8', 'Parameter 9'][d];
          }
        },
        yAxis: {
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          }
        }
      }
    };

    $scope.scatterdata = [
      {
        "key": "Model",
        "values": [
          [1, 0.200],
          [2, 1.199],
          [3, 2.198],
          [4, 3.198],
          [5, 0.198],
          [6, 4.198],
          [7, 3.198],
          [8, 2.595],
          [9, 1.195]
        ]
      },

      {
        "key": "Data",
        "values": [
          [1, 0.200],
          [2, 1.599],
          [3, 2.298],
          [4, 3.798],
          [5, 0.898],
          [6, 4.298],
          [7, 3.598],
          [8, 2.295],
          [9, 1.895]
        ]
      }

    ];


    $scope.linescatteroptions = {
      chart: {
        type: 'scatterPlusLineChart',
        height: 250,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 50
        },
        useInteractiveGuideline: true,
        sizeRange: [100, 100],
        xAxis: {
          axisLabel: 'Year'
        },
        yAxis: {
          axisLabel: 'Prevalence (%)',
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          },
          axisLabelDistance: 35
        }
      }
    };

    $scope.linescatterdata = [];

    $scope.doneEditingParameter = function () {
      console.log("I'm editing callback. Do what you have to do with me :(");
    };

    // save should save f parameters to the model: // calibrate/manual with f & dosave=true
    // preview should send f parameters to the model // calibrate/manual with f & dosave=true

    /*
     * Methods
     */

    $scope.previewManualCalibration = function () {
      Model.saveCalibrateManual({
        F: $scope.parameters.f
      }, function (response) {
        console.log(response);
      });
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: $scope.parameters.f,
        dosave: true
      }, function (response) {
        console.log(response);
      });
    };

    $scope.revertManualCalibration = function () {
      angular.extend($scope.parameters.f, $scope.parameters.cache.f);
    };

  });
});
