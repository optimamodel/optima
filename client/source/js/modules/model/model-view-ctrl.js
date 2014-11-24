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
          'Second-line ART initial value',
          'Second-line ART final value',
          'Second-line ART midpoint',
          'Second-line ART slope'
        ]
      },
      meta: meta,
      f: f,
      cache: {
        f: angular.copy(f),
        response: null
      }
    };

    $scope.types = [
      { id: 'prev', name: 'Prevalence', active: true, total: false },
      { id: 'daly', name: 'DALYs per year', active: false, total: false },
      { id: 'death', name: 'HIV-related deaths per year', active: false, total: false },
      { id: 'inci', name: 'New HIV infections per year', active: false, total: false }
    ];

    var getActiveOptions = function () {
      return _($scope.types).chain().where({ active: true }).pluck('id').value();
    };

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {};
    $scope.graphs = [];

    $scope.graphType = 'prev';

    var linescatteroptions = {
      height: 250,
      width: 400,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 50
      },
      xAxis: {
        axisLabel: 'Year',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: 'Prevalence (%)',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    var linescatterdata = {
      line: [],
      'scatter-error': []
  };

    $scope.doneEditingParameter = function () {
      console.log("I'm editing callback. Do what you have to do with me :(");
    };

    /*
     * Methods
     */

    var prepareGraphs = function (response, types) {
      var graphs = [];

      _(types).each(function (type) {
        var data = response[type];
        var scatterDataAvailable = data.pops.length === data.ydata.length;

        _(data.pops).each(function (population, populationIndex) {
          var graph = {
            options: angular.copy(linescatteroptions),
            data: angular.copy(linescatterdata)
          };

          graph.data.line = _(population).map(function (value, i) {
            //      x                 y
            return [response.tvec[i], value];
          });

          graph.options.xAxis.axisLabel = data.xlabel;
          graph.options.yAxis.axisLabel = data.ylabel;

          if (scatterDataAvailable) {
            graph.data['scatter-error'] = _(data.ydata[populationIndex]).chain()
              .map(function (value, i) {
                //      x                 y
                return [response.tvec[i], value];
              })
              .filter(function (value) {
                return !!value[1];
              })
              .value();
          }

          graphs.push(graph);
        });
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
          $scope.graphs = prepareGraphs(response, getActiveOptions());
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
      if (newValue && !_($scope.parameters.cache.response).isEmpty()) {
        $scope.graphs = prepareGraphs($scope.parameters.cache.response, $scope.graphType);
      }
    });

  });
});
