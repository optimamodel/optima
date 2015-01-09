define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval, Model, f, G, meta, info, CONFIG) {

    // use for export all data
    $scope.exportGraphs = {
      'name':'Model calibration',
      'controller':'ModelCalibration'
    };

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

    $scope.G = G;
    $scope.types = angular.copy(CONFIG.GRAPH_TYPES);
    $scope.calibrationStatus = false;

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {'timelimit':60};
    $scope.graphs = [];
    $scope.projectInfo = info;
    $scope.canDoFitting = $scope.projectInfo.can_calibrate;
    $scope.needData = !$scope.projectInfo.has_data;

    var lineScatterOptions = {
      title: 'Title',
      height: 200,
      width: 320,
      margin: CONFIG.GRAPH_MARGINS,
      xAxis: {
        axisLabel: 'Year',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: 'Prevalence (%)'
      }
    };

    var lineScatterData = {
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

    /**
     * Returns an array containing arrays with [x, y] for d3 line data.
     */
    var generateLineData = function(xData, yData) {
      return _(yData).map(function (value, i) {
        return [xData[i], value];
      });
    };

    /**
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

    /**
     * Returns a graph based on the provided yData.
     *
     * yData should be an array where each entry contains an array of all
     * y-values from one line.
     */
    var generateGraph = function(yData, xData, title) {
      var graph = {
        options: angular.copy(lineScatterOptions),
        data: angular.copy(lineScatterData),
        title: title
      };

      graph.options.title = title;

      graph.data.line = generateLineData(xData, yData.best);
      graph.data.area.lineHigh = generateLineData(xData, yData.high);
      graph.data.area.lineLow = generateLineData(xData, yData.low);

      return graph;
    };

    /**
     * Returns a financial graph.
     */
    var generateFinancialGraph = function(data) {
      var yData = {
        best: data.best, high: data.high, low: data.low
      };

      var graph = generateGraph(yData, data.xdata, data.title);

      graph.options.xAxis.axisLabel = data.xlabel;
      graph.options.yAxis.axisLabel = data.ylabel;

      return graph;
    };

    var prepareGraphs = function (response) {
      var graphs = [];

      if (!response) {
        return graphs;
      }

      _($scope.types.population).each(function (type) {

        var data = response[type.id];

        if (type.total) {

          var yData = {
            best: data.tot.best, high: data.tot.high, low: data.tot.low,
          };
          var graph = generateGraph(yData, response.tvec, data.tot.title);

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

            var yData = {
              best: population.best, high: population.high, low: population.low
            };
            var graph = generateGraph(yData, response.tvec, population.title);

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

      _($scope.types.financial).each(function (type) {
        // costcur = cost for current people living with HIV
        // costfut = cost for future people living with HIV
        // ann = annual costs
        // cum = cumulative costs
        if (type.annual) {
          var annualData = response[type.id].ann;
          graphs.push(generateFinancialGraph(annualData));
        }

        if (type.cumulative) {
          var cumulativeData = response[type.id].cum;
          graphs.push(generateFinancialGraph(cumulativeData));
        }
      });

      return graphs;
    };

    var updateGraphs = function (data) {
      if (data!== undefined && data!==null) {
        $scope.graphs = prepareGraphs(data);
        $scope.parameters.cache.response = data;
        $scope.canDoFitting = true;
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
            $scope.calibrationStatus = 'running';
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
          // Do not cancel timer yet
          if($scope.calibrationStatus) { // do nothing if there was no calibration
            $scope.calibrationStatus = 'requested to stop';
          }
        });
    };

    function stopTimer() {
      if ( angular.isDefined( autoCalibrationTimer ) ) {
        $interval.cancel(autoCalibrationTimer);
        autoCalibrationTimer = undefined;
        $scope.calibrationStatus = false;
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

    $scope.reportCalibrationStatus = function () {
      if ($scope.calibrationStatus) {
        return 'Calibration is ' + $scope.calibrationStatus;
      } else {
        return '';
      }
    };

    // The graphs are shown/hidden after updating the graph type checkboxes.
    $scope.$watch('types', function () {
      updateGraphs($scope.parameters.cache.response);
    }, true);

    $scope.reportDataEndError = function() {
      return "End year must be more than "+ $scope.G.dataend + ".";
    };

  });
});
