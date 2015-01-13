define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval, Model, f, G, meta, info, CONFIG, graphTypeFactory) {

    // use for export all data
    $scope.exportCharts = {
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
    $scope.types = graphTypeFactory.types;
    $scope.calibrationStatus = false;

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {'timelimit':60};
    $scope.charts = [];
    $scope.projectInfo = info;
    $scope.canDoFitting = $scope.projectInfo.can_calibrate;
    $scope.needData = !$scope.projectInfo.has_data;

    var defaultChartOptions = {
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
      }, updateCharts);
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
     * Returns a chart based on the provided yData.
     *
     * yData should be an array where each entry contains an array of all
     * y-values from one line.
     */
    var generateAreaChart = function(yData, xData, title) {
      var chart = {
        options: angular.copy(defaultChartOptions),
        data: angular.copy(lineScatterData),
        title: title
      };

      chart.options.title = title;

      chart.data.line = _.zip(xData, yData.best);
      chart.data.area.lineHigh = _.zip(xData, yData.high);
      chart.data.area.lineLow = _.zip(xData, yData.low);

      return chart;
    };

    /**
    * Returns a chart based on the provided yData.
    *
    * yData should be an array where each entry contains an array of all
    * y-values from one line.
    */
    var generateStackedAreaChart = function(yDataSet, xData, title, legend) {
      var chart = {
        options: angular.copy(defaultChartOptions),
        data: { areas: []},
        title: title
      };

      chart.options.title = title;
      chart.options.legend = legend;

      chart.data.areas = _(yDataSet).map(function(yData) {
        return _.zip(xData, yData);
      });

      return chart;
    };

    /**
     * Returns a financial chart.
     */
    var generateFinancialChart = function(data) {
      var yData = {
        best: data.best, high: data.high, low: data.low
      };

      var chart = generateAreaChart(yData, data.xdata, data.title);

      chart.options.xAxis.axisLabel = data.xlabel;
      chart.options.yAxis.axisLabel = data.ylabel;
      chart.type = 'lineScatterAreaChart';

      return chart;
    };

    var prepareCharts = function (response) {
      var charts = [];

      if (!response) {
        return charts;
      }

      _($scope.types.population).each(function (type) {

        var data = response[type.id];

        if (type.total) {

          var yData = {
            best: data.tot.best, high: data.tot.high, low: data.tot.low,
          };
          var chart = generateAreaChart(yData, response.tvec, data.tot.title);

          chart.options.xAxis.axisLabel = data.xlabel;
          chart.options.yAxis.axisLabel = data.tot.ylabel;
          chart.type = 'lineScatterAreaChart';

          // seems like ydata can either be an array of arrays for the
          // populations or a single array when it's used in overall
          if (!(data.ydata[0] instanceof Array)) {
            chart.data.scatter = generateScatterData(response.xdata, data.ydata);
          }

          charts.push(chart);
        }

        if (type.stacked) {
          var stackedAreaChart = generateStackedAreaChart(data.popstacked.pops,
            response.tvec, data.popstacked.title, data.popstacked.legend);

          stackedAreaChart.options.xAxis.axisLabel = data.xlabel;
          stackedAreaChart.options.yAxis.axisLabel = data.popstacked.ylabel;
          stackedAreaChart.type = 'stackedAreaChart';

          charts.push(stackedAreaChart);
        }

        // TODO: we're checking data because it could undefined ...
        if (type.byPopulation && data) {
          _(data.pops).each(function (population, populationIndex) {

            var yData = {
              best: population.best, high: population.high, low: population.low
            };
            var chart = generateAreaChart(yData, response.tvec, population.title);

            chart.options.xAxis.axisLabel = data.xlabel;
            chart.options.yAxis.axisLabel = population.ylabel;
            chart.type = 'lineScatterAreaChart';

            // seems like ydata can either be an array of arrays for the
            // populations or a single array when it's used in overall
            if (data.ydata[0] instanceof Array) {
              chart.data.scatter = generateScatterData(response.xdata, data.ydata[populationIndex]);
            }

            charts.push(chart);
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
          charts.push(generateFinancialChart(annualData));
        }

        if (type.cumulative) {
          var cumulativeData = response[type.id].cum;
          charts.push(generateFinancialChart(cumulativeData));
        }
      });

      return charts;
    };

    var updateCharts = function (data) {
      if (data!== undefined && data!==null) {
        $scope.charts = prepareCharts(data);
        $scope.parameters.cache.response = data;
        $scope.canDoFitting = true;
      }
    };

    $scope.simulate = function () {
      $http.post('/api/model/view', $scope.simulationOptions)
        .success(updateCharts);
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
            console.log("Cannot poll for calibration now");
          }
        });
    };

    function checkWorkingAutoCalibration() {
      $http.get('/api/model/working')
        .success(function(data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          } else {
            updateCharts(data.chart);
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
        .success(updateCharts);
    };

    $scope.revertCalibration = function () {
      $http.post('/api/model/calibrate/revert')
        .success(function(){ console.log("OK");});
    };

    $scope.previewManualCalibration = function () {
      Model.saveCalibrateManual({ F: prepareF($scope.parameters.f) }, updateCharts);
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        dosave: true
      }, updateCharts);
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

    // The charts are shown/hidden after updating the chart type checkboxes.
    $scope.$watch('types', function () {
      updateCharts($scope.parameters.cache.response);
    }, true);

    $scope.reportDataEndError = function() {
      return "End year must be more than "+ $scope.G.dataend + ".";
    };

  });
});
