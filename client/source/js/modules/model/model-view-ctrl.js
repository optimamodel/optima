define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ModelViewController', function ($scope, $http, $interval, Model, f, meta, CONFIG) {

    var prepareF = function (f) {
      var F = angular.copy(f);

      F.dx = _(F.dx).map(parseFloat);
      F.force = _(F.force).map(parseFloat);
      F.init = _(F.init).map(parseFloat);
      return F;
    };

    var transformedF = prepareF(f[0]);

    $scope.parameters = {
      types: {
        force: 'Force-of-infection for ',
        init: 'Initial prevalence for ',
        dx: [
          'Testing rate initial value',
          'Testing rate final value',
          'Testing rate midpoint',
          'Testing rate slope'
        ]
      },
      meta: meta,
      f: transformedF,
      cache: {
        f: angular.copy(transformedF),
        response: null
      }
    };

    $scope.types = angular.copy(CONFIG.GRAPH_TYPES);

    var getActiveOptions = function () {
      return _($scope.types).where({ active: true });
    };

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {'timelimit':60};
    $scope.graphs = [];

    var linescatteroptions = {
      height: 250,
      width: 400,
      margin: {
        top: 20,
        right: 10,
        bottom: 45,
        left: 70
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
      scatter: [],
      area: {}
    };

    $scope.doneEditingParameter = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        dosave: false
      }, updateGraphs);
    };

    /*
     * Returns an array containing arrays with [x, y] for d3 line data.
     */
    var generateLineData = function(xData, yData) {
      return _(yData).map(function (value, i) {
        return [xData[i], value];
      });
    };

    /*
    * Returns an array containing arrays with [x, y] for d3 scatter data.
    *
    * Empty entries are filtered out.
    */
    var generateScatterData = function(xData, yData) {
      return _(yData).chain()
        .map(function (value, i) {
          return [xData[i], value];
        })
        .filter(function (value) {
          return !!value[1];
        })
        .value();
    };

    var prepareGraphs = function (response) {
      var graphs = [], types;

      if (!response) {
        return graphs;
      }

      types = getActiveOptions();

      _(types).each(function (type) {

        var data = response[type.id];

        if (type.total) {
          var graph = {
            options: angular.copy(linescatteroptions),
            data: angular.copy(linescatterdata),
            type: type,
            title: data.tot.title
          };

          graph.data.line = generateLineData(response.tvec, data.tot.best);
          graph.data.area.lineHigh = generateLineData(response.tvec, data.tot.high);
          graph.data.area.lineLow = generateLineData(response.tvec, data.tot.low);

          graph.options.xAxis.axisLabel = data.xlabel;
          graph.options.yAxis.axisLabel = data.tot.ylabel;

          // seems like ydata can either be an array of arrays for the
          // populations or a single array when it's used in overall
          if (!(data.ydata[0] instanceof Array)) {
            graph.data.scatter = generateScatterData(response.xdata, data.ydata);
          }

          graphs.push(graph);
        }

        // TODO: we're checking data because it could undefined ...
        if (type.byPopulation && data) {
          _(data.pops).each(function (population, populationIndex) {
            var graph = {
              options: angular.copy(linescatteroptions),
              data: angular.copy(linescatterdata),
              type: type,
              title: population.title
            };

            graph.data.line = generateLineData(response.tvec, population.best);
            graph.data.area.lineHigh = generateLineData(response.tvec, population.high);
            graph.data.area.lineLow = generateLineData(response.tvec, population.low);

            graph.options.xAxis.axisLabel = data.xlabel;
            graph.options.yAxis.axisLabel = population.ylabel;

            // seems like ydata can either be an array of arrays for the
            // populations or a single array when it's used in overall
            if (data.ydata[0] instanceof Array) {
              graph.data.scatter = generateScatterData(response.xdata, data.ydata[populationIndex]);
            }

            graphs.push(graph);
          });
        }

      });

      return graphs;
    };

    var updateGraphs = function (data) {
      if (data!== undefined) {
        $scope.graphs = prepareGraphs(data);
        $scope.parameters.cache.response = data;
      }
    };

    $scope.simulate = function () {
      $http.post('/api/model/view', $scope.simulationOptions)
        .success(updateGraphs);
    };

	  var autoCalibrationTimer;
    $scope.startAutoCalibration = function () {
      $http.post('/api/model/calibrate/auto', $scope.simulationOptions)
        .success(function(data, status, headers, config) {
          if (data.status == "OK" && data.join) {
      // Keep polling for updated values after every 5 seconds till we get an error.
      // Error indicates that the model is not calibrating anymore.
            autoCalibrationTimer = $interval(checkWorkingAutoCalibration, 5000, 0, false);
          } else {
            console.log("Cannot poll for optimization now");
          }
        });
    };

    function checkWorkingAutoCalibration() {
      $http.get('/api/model/working')
        .success(function(data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          } else {
            updateGraphs(data.graph);
          }
        })
        .error(function(data, status, headers, config) {
          stopTimer();
        });
    }

    $scope.stopAutoCalibration = function () {
      $http.get('/api/model/calibrate/stop')
        .success(function(data) {
          // Cancel timer
          stopTimer();
        });
    };

    function stopTimer() {
      if ( angular.isDefined( autoCalibrationTimer ) ) {
        $interval.cancel(autoCalibrationTimer);
        autoCalibrationTimer = undefined;
      }
    }

    $scope.$on('$destroy', function() {
      // Make sure that the interval is destroyed too
      stopTimer();
    });

    $scope.saveCalibration = function () {
      $http.post('/api/model/calibrate/save')
        .success(updateGraphs);
    };

    $scope.revertCalibration = function () {
      $http.post('/api/model/calibrate/revert')
        .success(function(){ console.log("OK");});
    };

    $scope.previewManualCalibration = function () {
      Model.saveCalibrateManual({ F: prepareF($scope.parameters.f) }, updateGraphs);
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        dosave: true
      }, updateGraphs);
    };

    $scope.revertManualCalibration = function () {
      angular.extend($scope.parameters.f, $scope.parameters.cache.f);
    };

    $scope.onGraphTypeChange = function (type) {
      type.active = type.total || type.byPopulation;
      updateGraphs($scope.parameters.cache.response);
    };

  });
});
