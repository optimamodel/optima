define(['./module', 'angular', 'jquery', 'underscore'], function (module, angular, $, _) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval,
    Model, parameters, meta, info, CONFIG, graphTypeFactory, cfpLoadingBar) {

    $scope.projectInfo = info;
    $scope.canDoFitting = $scope.projectInfo.can_calibrate;
    $scope.needData = !$scope.projectInfo.has_data;
    $scope.$on('onAfterRender', function (e){ $scope.onAfterGraphRender() });
    $scope.tallestGraphHeight = 0;
    $scope.renderedGraphs = 0; // counts how many Graphs are rendered (see onAfterGraphRender for more on this)

    var prepareF = function (f) {
      var F = angular.copy(f);

      F.dx = _(F.dx).map(parseFloat);
      F.force = _(F.force).map(parseFloat);
      F.init = _(F.init).map(parseFloat);
      F.popsize = _(F.popsize).map(parseFloat);
      return F;
    };

    var prepareM = function(m) {
      _(m).each(function (parameter) {
        parameter.data = parseFloat(parameter.data);
      });
      return m;
    };

    var transformedF = $scope.needData? {} : prepareF(parameters.F[0]);

    $scope.parameters = {
      types: {
        force: 'Relative force-of-infection for ',
        popsize: 'Initial population size for ',
        init: 'Initial prevalence for ',
        dx: [
          'Overall population initial relative testing rate',
          'Overall population final relative testing rate',
          'Year of mid change in overall population testing rate',
          'Testing rate slope parameter'
        ]
      },
      meta: meta,
      f: transformedF,
      m: parameters.M,
      cache: {
        f: angular.copy(transformedF),
        m: angular.copy(parameters.M),
        response: null
      }
    };

    $scope.types = graphTypeFactory.types;
    // reset graph types every time you come to this page
    angular.extend($scope.types, angular.copy(CONFIG.GRAPH_TYPES));
    // for calibration the overall charts should not be shown by default
    _($scope.types.population).each(function(entry) {
      if (!_(['tx1', 'tx2', 'force']).contains(entry.id)) {
        entry.total = false;
      }
    });
    // for calibration the overall cost charts should not be shown by default
    _($scope.types.costs).each(function(entry) {
      entry.total = false;
    });

    $scope.calibrationStatus = false;

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {'timelimit':60};
    $scope.charts = [];
    $scope.hasStackedCharts = false;
    $scope.hasCharts = false;

    var defaultChartOptions = {
      title: 'Title',
      height: 200,
      width: 320,
      margin: CONFIG.GRAPH_MARGINS,
      xAxis: {
        axisLabel: 'Year'
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
        M: prepareM($scope.parameters.m),
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

      $scope.hasStackedCharts = true;
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

        if (type.total && data) {

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

        if (type.stacked) {
          var stackedAreaChart = generateStackedAreaChart(data.popstacked.pops,
            response.tvec, data.popstacked.title, data.popstacked.legend);

          stackedAreaChart.options.xAxis.axisLabel = data.xlabel;
          stackedAreaChart.options.yAxis.axisLabel = data.popstacked.ylabel;
          stackedAreaChart.type = 'stackedAreaChart';

          charts.push(stackedAreaChart);
        }
      });

      // annual cost charts
      _(['existing', 'future', 'total']).each(function(type) {
        var chartData = response.costann[type][$scope.types.activeAnnualCost];
        var isActive = $scope.types.costs[0][type];
        if (chartData && isActive) {
          charts.push(generateFinancialChart(chartData));
        }
      });

      var stackedAnnualData = response.costann.stacked[$scope.types.activeAnnualCost];
      var stackedAnnualCostIsActive = $scope.types.costs[0].stacked;
      if (stackedAnnualData && stackedAnnualCostIsActive) {
        var stackedAreaChart = generateStackedAreaChart(stackedAnnualData.costs,
          response.tvec, stackedAnnualData.title, stackedAnnualData.legend);
        stackedAreaChart.options.xAxis.axisLabel = 'Year';
        stackedAreaChart.options.yAxis.axisLabel = stackedAnnualData.ylabel;
        stackedAreaChart.type = 'stackedAreaChart';
        charts.push(stackedAreaChart);
      }

      // cumulative cost charts
      _(['existing', 'future', 'total']).each(function(type) {
        var chartData = response.costcum[type];
        var isActive = $scope.types.costs[1][type];
        if (chartData && isActive) {
          charts.push(generateFinancialChart(chartData));
        }
      });

      var stackedCumulativeData = response.costcum.stacked;
      var stackedCumulativeCostIsActive = $scope.types.costs[1].stacked;
      if (stackedCumulativeData && stackedCumulativeCostIsActive) {
        var stackedCumulativeChart = generateStackedAreaChart(
          stackedCumulativeData.costs, response.tvec,
          stackedCumulativeData.title, stackedCumulativeData.legend);
        stackedCumulativeChart.options.xAxis.axisLabel = 'Year';
        stackedCumulativeChart.options.yAxis.axisLabel = stackedCumulativeData.ylabel;
        stackedCumulativeChart.type = 'stackedAreaChart';
        charts.push(stackedCumulativeChart);
      }

      // commitments
      var commitChartData = response.commit[$scope.types.activeAnnualCost];
      var commitIsActive = $scope.types.costs[2].checked;
      if (commitChartData && commitIsActive) {
        charts.push(generateFinancialChart(commitChartData));
      }

      return charts;
    };

    var updateCharts = function (data) {
      if (data!== undefined && data!==null && data.graph !== undefined) {
        graphTypeFactory.enableAnnualCostOptions($scope.types, data.graph);

        $scope.charts = prepareCharts(data.graph);
        $scope.hasCharts = ($scope.charts.length>0);
        $scope.parameters.cache.response = data;
        $scope.canDoFitting = true;
        if (data.F){
          var f = prepareF(data.F[0]);
          $scope.parameters.f = f;
          $scope.parameters.cache.f = angular.copy(f);
        }
        if (data.M) {
          $scope.parameters.m = data.M;
          $scope.parameters.cache.m = angular.copy(data.M);
        }
      }
    };

    $scope.simulate = function () {
      $http.post('/api/model/view', $scope.simulationOptions)
        .success(updateCharts);
    };


    if($scope.needData === false){
      $scope.simulate();
    }

    var autoCalibrationTimer;
    $scope.startAutoCalibration = function () {
      $http.post('/api/model/calibrate/auto', $scope.simulationOptions,{ignoreLoadingBar: true})
        .success(function(data, status, headers, config) {
          if (data.status == "OK" && data.join) {
      // Keep polling for updated values after every 5 seconds till we get an error.
      // Error indicates that the model is not calibrating anymore.
            autoCalibrationTimer = $interval(checkWorkingAutoCalibration, 5000, 0, false);
            $scope.calibrationStatus = 'running';
            $scope.errorText = '';

            // start cfpLoadingBar loading
            // calculate the number of ticks in timelimit
            var val = ($scope.simulationOptions.timelimit * 1000) / 250;
            // callback function in start to be called in place of _inc()
            cfpLoadingBar.start(function () {
              if (cfpLoadingBar.status() >= 0.95) {
                return;
              }
              var pct = cfpLoadingBar.status() + (0.95/val);
              cfpLoadingBar.set(pct);
            });
          } else {
            console.log("Cannot poll for calibration now");
          }
        });
    };

    function checkWorkingAutoCalibration() {
      $http.get('/api/model/working',{ignoreLoadingBar: true})
        .success(function(data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          }
          updateCharts(data); // now when we might run continuous calibration, this might be the only chance to update the charts.
        })
        .error(function(data, status, headers, config) {
          if (data && data.exception) {
            $scope.errorText = data.exception;
          }
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
        cfpLoadingBar.complete();
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
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        M: prepareM($scope.parameters.m) }, updateCharts);
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        M: prepareM($scope.parameters.m),
        dosave: true
      }, updateCharts);
    };

    $scope.revertManualCalibration = function () {
      angular.extend($scope.parameters.f, $scope.parameters.cache.f);
      angular.extend($scope.parameters.m, $scope.parameters.cache.m);
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

    // Returns the value of the tallest chart.
    $scope.getMaxChartHeight = function () {
      return $(_.max($('.chart-container'), function (element) {
          return $(element).height();
          })).height();
    };

    // Makes all charts to be aHeight pixels tall.
    $scope.updateChartHeightsTo = function (aHeight) {
      $('.chart-container').each(function(i, element){ 
        $(element).height(aHeight)});
    };    

    // If all graphs were rendered, this will set them all with the height value of the tallest of them.
    $scope.setSameGraphsHeight = function () {    
      if($scope.renderedGraphs == $('.chart-container').length) $scope.updateChartHeightsTo($scope.getMaxChartHeight());
    };

    /**
    * This controller has its view just rendered, react accordingly.
    */
    $scope.onAfterGraphRender = function () {
      $scope.renderedGraphs = $scope.renderedGraphs + 1;
      $scope.setSameGraphsHeight();
    };
  });
});
