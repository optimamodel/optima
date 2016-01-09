define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ModelCalibrationController', function ($scope, $http, $interval,
    Model, parameters, meta, info, CONFIG, typeSelector, cfpLoadingBar, calibration, modalService) {

    console.log('info', info);

    // In case there is no model data the controller only needs to show the
    // warning that the user should upload a spreadsheet with data.

    var activeProjectInfo = info.data;

    if (!activeProjectInfo.has_data) {
      $scope.missingModelData = true;
      return;
    }

    $http.get('/api/project/' + activeProjectInfo.id + '/parsets').
      success(function (response) {
        var parsets = response.parsets;
        if(parsets) {
          parsets.forEach(function(parset) {
            console.log('parset', parset);
            $http.get('/api/parset/' + parset.id + '/calibration').
            then(function (response) {
              console.log('response1', response);
              $scope.chart = response.calibration.graph[0];
              console.log('plotted chart');
            },function(response) {
              console.log('response2', response);
              $scope.chart = response.calibration.graph[0];
              console.log('plotted chart');
            })
            ;
          });
        }
      });

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

    var initialize = function() {
      $scope.projectInfo = activeProjectInfo;
      $scope.canDoFitting = false;
      $scope.hasSpreadsheet = activeProjectInfo.data_upload_time ? true : false;

      $scope.types = typeSelector.types;

      // for calibration the overall charts should not be shown by default
      _($scope.types.population).each(function(entry) {
        if (!_(['tx1', 'tx2', 'force']).contains(entry.id)) {
          entry.total = false;
        }
      });
      // for calibration the overall cost charts should not be shown by default
      _($scope.types.costsKeys).each(function(key) {
        if ($scope.types.costs[key].total!== undefined) {
          $scope.types.costs[key].total = false; // this does not seem to work, but it's beyond me why - AN
        }
      });

      $scope.calibrationStatus = false;

      $scope.enableManualCalibration = false;

      $scope.simulationOptions = {'timelimit': 60};
      $scope.charts = [];
      $scope.hasStackedCharts = false;
      $scope.parameters = {
        types: {
          force: 'Relative force-of-infection for ',
          inhomo: 'Inhomogeneity in force-of-infection for ',
          popsize: 'Initial population size for ',
          init: 'Initial prevalence for ',
          dx: [
            'Overall population initial relative testing rate',
            'Overall population final relative testing rate',
            'Year of mid change in overall population testing rate',
            'Testing rate slope parameter'
          ]
        },
        // meta: meta.data
      };
      angular.extend($scope.parameters, calibration.toScopeParameters(parameters));

      $scope.simulate();
    };

    /**
     * Makes the backend to reload the spreadsheet and reloads the page after that.
     */
    $scope.reloadSpreadsheet = function () {
      if(!$scope.hasSpreadsheet) {
        var message = "Sorry, this project was created without uploading a spreadsheet and therefore can not be reloaded.";
        modalService.inform(undefined, undefined, message);
      } else {
        $http.get('/api/model/reloadSpreadsheet/' + activeProjectInfo.id)
          .success(function (response) {
            window.location.reload();
          });
      }
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
        data: {
          lines: [],
          scatter: [],
          areas: []
        },
        title: title
      };

      chart.options.title = title;
      chart.options.linesStyle = ['__color-black'];

      chart.data.lines.push(_.zip(xData, yData.best));
      chart.data.areas.push({
        highLine: _.zip(xData, yData.high),
        lowLine: _.zip(xData, yData.low)
      });

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
        data: { areas: [] },
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
      chart.type = 'lineAreaScatterChart';

      return chart;
    };


    var prepareCharts = function (response) {
      var charts = [];

//      var typesCostann = _($scope.types.costs).filter(function (item) {return item.id == "costann";})[0];
//      var typesCostcum = _($scope.types.costs).filter(function (item) {return item.id == "costcum";})[0];
//      var typesCommit = _($scope.types.costs).filter(function (item) {return item.id == "commit";})[0];

      if (!response) {
        return charts;
      }
      _($scope.types.population).each(function (type) {
        var data = response[type.id];

        if (type.total && data) {

          var yData = {
            best: data.tot.best,
            high: data.tot.high,
            low: data.tot.low
          };
          var chart = generateAreaChart(yData, response.tvec, data.tot.title);

          chart.options.xAxis.axisLabel = data.xlabel;
          chart.options.yAxis.axisLabel = data.tot.ylabel;
          chart.type = 'lineAreaScatterChart';

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
            chart.type = 'lineAreaScatterChart';

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

      _($scope.types.possibleKeys).each(function(type) {
        var isActive = $scope.types.costs.costann[type];
        if (isActive) {
          var chartData = response.costann[type][$scope.types.activeAnnualCost];
          if (chartData) {
            charts.push(generateFinancialChart(chartData));
          }
        }
      });

      var stackedAnnualData = response.costann.stacked[$scope.types.activeAnnualCost];
      var stackedAnnualCostIsActive = $scope.types.costs.costann.stacked;
      if (stackedAnnualData && stackedAnnualCostIsActive) {
        var stackedAreaChart = generateStackedAreaChart(stackedAnnualData.costs,
          response.tvec, stackedAnnualData.title, stackedAnnualData.legend);
        stackedAreaChart.options.xAxis.axisLabel = 'Year';
        stackedAreaChart.options.yAxis.axisLabel = stackedAnnualData.ylabel;
        stackedAreaChart.type = 'stackedAreaChart';
        charts.push(stackedAreaChart);
      }

      // cumulative cost charts
      _($scope.types.possibleKeys).each(function(type) {
        var chartData = response.costcum[type];
        var isActive = $scope.types.costs.costcum[type];
        if (isActive) {
          if (chartData) {
            charts.push(generateFinancialChart(chartData));
          }
        }
      });

      var stackedCumulativeData = response.costcum.stacked;
      var stackedCumulativeCostIsActive = $scope.types.costs.costcum.stacked;
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
      var commitIsActive = $scope.types.costs.commit.checked;
      if (commitIsActive) {
        var commitChartData = response.commit[$scope.types.activeAnnualCost];
        if (commitChartData) {
          charts.push(generateFinancialChart(commitChartData));
        }
      }
      return charts;
    };

    /**
     * Stores the last saved data for later retrieval & updates the charts with
     * the received data.
     */
    var storeSavedCalibrationAndUpdate = function (data) {
      calibration.storeLastSavedResponse(data);
      updateChartsAndParameters(data);
    };

    var updateChartsAndParameters = function (data) {
      if (data!== undefined && data!==null && data.graph !== undefined) {
        calibration.storeLastPreviewResponse(data);

        typeSelector.enableAnnualCostOptions($scope.types, data.graph);

        $scope.charts = prepareCharts(data.graph);
        $scope.canDoFitting = true;

        angular.extend($scope.parameters, calibration.toScopeParameters(data));
      }
    };

    $scope.simulate = function () {
    //  $http.post('/api/model/view', $scope.simulationOptions)
    //    .success(storeSavedCalibrationAndUpdate);
    };

    var autoCalibrationTimer;
    $scope.startAutoCalibration = function () {
      $http.post('/api/model/calibrate/auto', $scope.simulationOptions,{ignoreLoadingBar: true})
        .success(function(data, status, headers, config) {
          if (data.join) {
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
          updateChartsAndParameters(data); // now when we might run continuous calibration, this might be the only chance to update the charts.
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
        .success(storeSavedCalibrationAndUpdate);
    };

    $scope.revertCalibration = function () {
      $http.post('/api/model/calibrate/revert')
        .success(storeSavedCalibrationAndUpdate);
    };

    $scope.saveManualCalibration = function () {
      var data = calibration.toRequestParameters($scope.parameters, true);
      Model.runManualCalibration(data, storeSavedCalibrationAndUpdate);
    };

    $scope.doneEditingParameter = function () {
      var data = calibration.toRequestParameters($scope.parameters, false);
      Model.runManualCalibration(data, updateChartsAndParameters);
    };

    $scope.revertManualCalibration = function () {
      updateChartsAndParameters(calibration.lastSavedResponse());
    };

    $scope.reportCalibrationStatus = function () {
      if ($scope.calibrationStatus) {
        return 'Calibration is ' + $scope.calibrationStatus;
      } else {
        return '';
      }
    };

    initialize();

    // The charts are shown/hidden after updating the chart type checkboxes.
    $scope.$watch('types', function () {
      updateChartsAndParameters(calibration.lastPreviewResponse());
    }, true);

  });
});
