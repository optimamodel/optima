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
        f: angular.copy(f),
        response: null
      }
    };

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {};
    $scope.graphs = [];

    $scope.graphType = 'prev';

    var linescatteroptions = {
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

    var linescatterdata = [
      {
        values: [],
        key: 'Model',
        color: '#ff7f0e'
      }
    ];

    $scope.doneEditingParameter = function () {
      console.log("I'm editing callback. Do what you have to do with me :(");
    };

    /*
     * Methods
     */

    var prepareGraphs = function (response, type) {
      var graphs = [];

      _(response[type].pops).each(function (population) {
        var graph = {
          options: angular.copy(linescatteroptions),
          data: angular.copy(linescatterdata)
        };

        graph.data[0].values = _(population).map(function (value, i) {
          return {
            x: value,
            y: response.tvec[i]
          };
        });

        graphs.push(graph);
      });

      return graphs;
    };

    var prepareF = function (f) {
      var F = angular.copy(f);

      F.dx = _(F.dx).map(parseFloat);
      F.force = _(F.force).map(parseFloat);
      F.init = _(F.init).map(parseFloat);
      F.tx1 = _(F.tx1).map(parseFloat);
      F.tx2 = _(F.tx2).map(parseFloat);

      return F;
    };

    $scope.simulate = function () {
      $http.post('/api/model/view', $scope.simulationOptions)
        .success(function (response) {
          $scope.graphs = prepareGraphs(response, $scope.graphType);
          $scope.parameters.cache.response = response;
        });
    };

    $scope.previewManualCalibration = function () {
      Model.saveCalibrateManual({ F: prepareF($scope.parameters.f) },
        function (response) {
          $scope.graphs = prepareGraphs(response, $scope.graphType);
          $scope.parameters.cache.response = response;
        });
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        dosave: true
      }, function (response) {
        $scope.graphs = prepareGraphs(response, $scope.graphType);
        $scope.parameters.cache.response = response;
      });
    };

    $scope.revertManualCalibration = function () {
      angular.extend($scope.parameters.f, $scope.parameters.cache.f);
    };

    $scope.$watch('graphType', function (newValue) {
      if (newValue) {
        $scope.graphs = prepareGraphs($scope.parameters.cache.response, $scope.graphType);
      }
    });

  });
});
