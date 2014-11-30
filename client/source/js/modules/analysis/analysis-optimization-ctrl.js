define([
  './module',
  'angular',
  'd3'
], function (module, angular, d3) {
  'use strict';

  module.controller('AnalysisOptimizationController', function ($scope, $http, $interval, meta, CONFIG) {

      $scope.meta = meta;
      $scope.types = angular.copy(CONFIG.GRAPH_TYPES);

      // cache placeholder
      var cachedResponse = null;

      // Set defaults
      $scope.params = {};

      // Default time limit is 10 seconds
      $scope.params.timelimit = 60;

      // Objectives
      $scope.params.objectives = {};
      $scope.params.objectives.what = 'outcome';

      // Outcome objectives defaults
      $scope.params.objectives.outcome = {};
      $scope.params.objectives.outcome.inci = false;
      $scope.params.objectives.outcome.daly = false;
      $scope.params.objectives.outcome.death = false;
      $scope.params.objectives.outcome.cost = false;

      // Money objectives defaults
      $scope.params.objectives.money = {};
      $scope.params.objectives.money.objectives = {};
      $scope.params.objectives.money.objectives.dalys = {};
      $scope.params.objectives.money.objectives.dalys.use = false;
      $scope.params.objectives.money.objectives.deaths = {};
      $scope.params.objectives.money.objectives.deaths.use = false;
      $scope.params.objectives.money.objectives.inci = {};
      $scope.params.objectives.money.objectives.inci.use = false;
      $scope.params.objectives.money.objectives.inciinj = {};
      $scope.params.objectives.money.objectives.inciinj.use = false;
      $scope.params.objectives.money.objectives.incisex = {};
      $scope.params.objectives.money.objectives.incisex.use = false;
      $scope.params.objectives.money.objectives.mtct = {};
      $scope.params.objectives.money.objectives.mtct.use = false;
      $scope.params.objectives.money.objectives.mtctbreast = {};
      $scope.params.objectives.money.objectives.mtctbreast.use = false;
      $scope.params.objectives.money.objectives.mtctnonbreast = {};
      $scope.params.objectives.money.objectives.mtctnonbreast.use = false;

      // Default program weightings
      $scope.params.objectives.money.costs = {};
      $scope.programs = meta.progs.long;
      $scope.programCodes = meta.progs.code;

      for ( var i = 0; i < meta.progs.code.length; i++ ) {
        $scope.params.objectives.money.costs[meta.progs.code[i]] = 100;
      }

      // Constraints Defaults
      $scope.params.constraints = {};
      $scope.params.constraints.txelig = 1;
      $scope.params.constraints.dontstopart = true;

      $scope.params.constraints.decrease = {};
      $scope.params.constraints.coverage = {};

      for ( var i = 0; i < meta.progs.code.length; i++ ) {
        $scope.params.constraints.decrease[meta.progs.code[i]] = {};
        $scope.params.constraints.decrease[meta.progs.code[i]].use = false;
        $scope.params.constraints.decrease[meta.progs.code[i]].by = 100;

        $scope.params.constraints.coverage[meta.progs.code[i]] = {};
        $scope.params.constraints.coverage[meta.progs.code[i]].use = false;
        $scope.params.constraints.coverage[meta.progs.code[i]].level = 0;
        $scope.params.constraints.coverage[meta.progs.code[i]].year = 2030;
      }

      $scope.pieoptions = {
          chart: {
              type: 'pieChart',
              height: 350,
              x: function(d){return d.key;},
              y: function(d){return d.y;},
              showLabels: false,
              transitionDuration: 500,
              labelThreshold: 0.01,
              legend: {
                  margin: {
                      top: 5,
                      right: 35,
                      bottom: 5,
                      left: 0
                  }
              }
          }
      };

      $scope.lineoptions = {
        chart: {
          type: 'lineChart',
          height: 200,
          margin: {
            top: 20,
            right: 20,
            bottom: 40,
            left: 55
          },
          useInteractiveGuideline: true,
          dispatch: {},
          xAxis: {
            axisLabel: 'Year',
            tickFormat: function (d) {
              return d3.format('d')(d);
            }
          },
          yAxis: {
            axisLabel: 'Value',
            axisLabelDistance: 30,
            tickFormat: function (d) {
              return d3.format(',.2f')(d);
            }
          },
          transitionDuration: 250
        },
        title: {
          enable: true,
          text: 'Title for Line Chart'
        }
      };

    var linedataTpl = {
      "values": [
        // {"x": 0, "y": 0, "series": 0},
      ],
      "key": "Sine Wave",
      "color": "#ff7f0e",
      "seriesIndex": 0
    };

    var getActiveOptions = function () {
      return _($scope.types).where({ active: true });
    };

    /*
     * Returns an array containing arrays with [x, y] for d3 line data.
     */
    var generateLineData = function(xData, yData, series) {
      return _(yData).map(function (value, i) {
        return { x: xData[i], y: value, series: series };
      });
    };

    var prepareLineCharts = function (response) {
      var graphs = [], types;

      if (!response) {
        return graphs;
      }

      types = getActiveOptions();

      _(types).each(function (type) {

        var data = response[type.id];

        if (type.total) {
          var graph = {
            options: angular.copy($scope.lineoptions),
            data: [],
            type: type,
            title: type.name + ' - Overall'
          };

          graph.data.push({
            "values": generateLineData(response.tvec, data.tot.data[0], 0),
            "key": "1",
            "color": "#0000FF",
            "seriesIndex": 0
          });

          graph.data.push({
            "values": generateLineData(response.tvec, data.tot.data[1], 1),
            "key": "2",
            "color": "#000000",
            "seriesIndex": 1
          });


          graph.options.chart.xAxis.axisLabel = data.xlabel;
          graph.options.chart.yAxis.axisLabel = data.tot.ylabel;
          graph.options.title.text = data.tot.title;

          graphs.push(graph);
        }

        // TODO: we're checking data because it could undefined ...
        if (type.byPopulation && data) {
          _(data.pops).each(function (population, populationIndex) {
            var graph = {
              options: angular.copy($scope.lineoptions),
              data: [],
              type: type
            };

            graph.data.push({
              "values": generateLineData(response.tvec, population.data[0], 0),
              "key": "2",
              "color": "#000000",
              "seriesIndex": 0
            });

            graph.data.push({
              "values": generateLineData(response.tvec, population.data[1], 1),
              "key": "2",
              "color": "#0000FF",
              "seriesIndex": 1
            });

            graph.options.chart.xAxis.axisLabel = data.xlabel;
            graph.options.chart.yAxis.axisLabel = population.ylabel;
            graph.options.title.text = population.title;

            graphs.push(graph);
          });
        }

      });

      return graphs;
    };

    // updates pies charts data
    var preparePieCharts = function (data) {
      if (data.pie1 === undefined || data.pie2 === undefined) return;
      $scope.piedata1 = _(data.pie1.val).map(function (value, index) {
        return { y: value, key: data.legend[index] };
      });

      $scope.piedata2 = _(data.pie2.val).map(function (value, index) {
        return { y: value, key: data.legend[index] };
      });
    };

    // makes line graphs to recalculate and redraw
    var updateLineGraphs = function (data) {
      $scope.lines = prepareLineCharts(data);
    };

    // makes all graphs to recalculate and redraw
    var updateGraphs = function (data) {
      if (data.graph !== undefined && data.pie !== undefined) {
        cachedResponse = data;  
        console.log(data);
        updateLineGraphs(data.graph);
        preparePieCharts(data.pie);
      }
    };




    var optimizationTimer;

    $scope.startOptimization = function () {
      $http.post('/api/analysis/optimization/start', $scope.params)
        .success(function(data, status, headers, config) {
          if (data.status == "OK" && data.join) {
      // Keep polling for updated values after every 5 seconds till we get an error.
      // Error indicates that the model is not calibrating anymore.
            optimizationTimer = $interval(checkWorkingOptimization, 5000, 0, false);
          } else {
            console.log("Cannot poll for optimization now");
          }
        });
    };

    function checkWorkingOptimization() {
      $http.get('/api/analysis/optimization/working')
        .success(function(data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          } else {
            updateGraphs(data);
          }
        })
        .error(function(data, status, headers, config) {
          stopTimer();
        });
    }

    $scope.stopOptimization = function () {
      $http.get('/api/analysis/optimization/stop')
        .success(function(data) {
          // Cancel timer
          stopTimer();
        });
    };

    function stopTimer() {
      if ( angular.isDefined( optimizationTimer ) ) {
        $interval.cancel(optimizationTimer);
        optimizationTimer = undefined;
      }
    }

    $scope.$on('$destroy', function() {
      // Make sure that the interval is destroyed too
      stopTimer();
    });

    $scope.saveOptimization = function () {
      $http.post('/api/model/optimization/save')
        .success(updateGraphs);
    };

    $scope.revertOptimization = function () {
      $http.post('/api/model/optimization/revert')
        .success(function(){ console.log("OK");});
    };

    $scope.onGraphTypeChange = function (type) {
      type.active = type.total || type.byPopulation;

      if (!cachedResponse || !cachedResponse.graph) return;

      updateLineGraphs(cachedResponse.graph);
    };

  });
});
