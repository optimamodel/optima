define([
  './module',
  'angular',
  'd3'
], function (module, angular, d3) {
  'use strict';

  module.controller('AnalysisOptimizationController', function ($scope, $http, $interval, meta, CONFIG) {

      $scope.meta = meta;
      $scope.types = angular.copy(CONFIG.GRAPH_TYPES);

      // use for export all data
      $scope.exportGraphs = {
        'name':'Optimization analyses',
        'controller':'AnalysisOptimization'
      };

      var statusEnum = {
        NOT_RUNNING: { text: "", isActive: false },
        RUNNING: { text: "Optimization is running", isActive: true },
        REQUESTED_TO_STOP : { text:"Optimization is requested to stop", isActive: true }
      };

      $scope.optimizationStatus = statusEnum.NOT_RUNNING;

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
      $scope.programCodes = meta.progs.short;

      for ( var i = 0; i < meta.progs.short.length; i++ ) {
        $scope.params.objectives.money.costs[meta.progs.short[i]] = 100;
      }

      // Constraints Defaults
      $scope.params.constraints = {};
      $scope.params.constraints.txelig = 1;
      $scope.params.constraints.dontstopart = true;

      $scope.params.constraints.decrease = {};
      $scope.params.constraints.increase = {};
      $scope.params.constraints.coverage = {};

      // Initialize program constraints models
      for ( var i = 0; i < meta.progs.short.length; i++ ) {
        $scope.params.constraints.decrease[meta.progs.short[i]] = {};
        $scope.params.constraints.decrease[meta.progs.short[i]].use = false;
        $scope.params.constraints.decrease[meta.progs.short[i]].by = 100;

        $scope.params.constraints.increase[meta.progs.short[i]] = {};
        $scope.params.constraints.increase[meta.progs.short[i]].use = false;
        $scope.params.constraints.increase[meta.progs.short[i]].by = 100;

        $scope.params.constraints.coverage[meta.progs.short[i]] = {};
        $scope.params.constraints.coverage[meta.progs.short[i]].use = false;
        $scope.params.constraints.coverage[meta.progs.short[i]].level = 0;
        $scope.params.constraints.coverage[meta.progs.short[i]].year = undefined;
      }

    var linesStyle = ['__blue', '__green', '__red', '__orange', '__violet',
      '__black', '__light-orange', '__light-green'];

    var linesGraphOptions = {
      height: 200,
      width: 320,
      margin: CONFIG.GRAPH_MARGINS,
      linesStyle: linesStyle,
      xAxis: {
        axisLabel: 'Year',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: ''
      }
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
    * Returns an graph based on the provided yData.
    *
    * yData should be an array where each entry contains an array of all
    * y-values from one line.
    */
    var generateGraph = function(yData, xData, title, legend, xLabel, yLabel) {
      var linesGraphData = {
        lines: [],
        scatter: []
      };

      var graph = {
        options: angular.copy(linesGraphOptions),
        data: angular.copy(linesGraphData)
      };

      graph.options.title = title;
      graph.options.legend = legend;

      graph.options.xAxis.axisLabel = xLabel;
      graph.options.yAxis.axisLabel = yLabel;

      _(yData).each(function(lineData) {
        graph.data.lines.push(generateLineData(xData, lineData));
      });

      return graph;
    };

    // updates pies charts data
    /**
     *
     */
    var prepareRadarChart = function (data) {

      if (data.pie1 === undefined || data.pie2 === undefined) return;

      var graphData = [{axes: []}, {axes: []}];

      var options = {
        legend: [],
        linesStyle: linesStyle
      };

      graphData[0].axes = _(data.pie1.val).map(function (value, index) {
        return { value: value, axis: data.legend[index] };
      });
      options.legend.push(data.pie1.name);

      graphData[1].axes = _(data.pie2.val).map(function (value, index) {
        return { value: value, axis: data.legend[index] };
      });
      options.legend.push(data.pie2.name);

      $scope.radarData = graphData;
      $scope.radarOptions = options;
    };

    /**
     * Regenerate graphs based on the response and type settings in the UI.
     */
    var prepareOptimisationGraphs = function (response) {
      var graphs = [];

      if (!response) {
        return graphs;
      }

      _($scope.types.population).each(function (type) {

        var data = response[type.id];
        if (data !== undefined) {

          // generate graphs showing the overall data for this type
          if (type.total) {
            var graph = generateGraph(
              data.tot.data, response.tvec,
              data.tot.title, data.tot.legend,
              data.xlabel, data.tot.ylabel
            );
            graphs.push(graph);
          }

          // generate graphs for this type for each population
          if (type.byPopulation) {
            _(data.pops).each(function (population) {
              var graph = generateGraph(
                population.data, response.tvec,
                population.title, population.legend,
                data.xlabel, population.ylabel
              );
              graphs.push(graph);
            });
          }
        }
      });

      return graphs;
    };

    /**
     * Returns a financial graph.
     */
    var generateFinancialGraph = function(data) {
      var graph = generateGraph(data.data, data.xdata, data.title, data.legend, data.xlabel, data.ylabel);
      return graph;
    };

    var prepareFinancialGraphs = function(graphData) {
      var graphs = [];

      _($scope.types.financial).each(function (type) {
        // costcur = cost for current people living with HIV
        // costfut = cost for future people living with HIV
        // ann = annual costs
        // cum = cumulative costs
        if (graphData[type.id] !== undefined) {
          if (type.annual && graphData[type.id].ann) {
            var annualData = graphData[type.id].ann;
            graphs.push(generateFinancialGraph(annualData));
          }

          if (type.cumulative && graphData[type.id].cum) {
            var cumulativeData = graphData[type.id].cum;
            graphs.push(generateFinancialGraph(cumulativeData));
          }
        }
      });
      return graphs;
    };

    // makes all graphs to recalculate and redraw
    var updateGraphs = function (data) {
      if (data.graph !== undefined && data.pie !== undefined) {
        cachedResponse = data;
        $scope.optimisationGraphs = prepareOptimisationGraphs(data.graph);
        $scope.financialGraphs = prepareFinancialGraphs(data.graph);
        $scope.radarChart = prepareRadarChart(data.pie);
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
            $scope.optimizationStatus = statusEnum.RUNNING;
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
          // Do not cancel timer yet, if the optimization is running
          if ($scope.optimizationStatus) {
            $scope.optimizationStatus = statusEnum.REQUESTED_TO_STOP;
          }
        });
    };

    function stopTimer() {
      if ( angular.isDefined( optimizationTimer ) ) {
        $interval.cancel(optimizationTimer);
        optimizationTimer = undefined;
        $scope.optimizationStatus = statusEnum.NOT_RUNNING;
      }
    }

    $scope.$on('$destroy', function() {
      // Make sure that the interval is destroyed too
      stopTimer();
    });

    $scope.saveOptimization = function () {
      $http.post('/api/analysis/optimization/save')
        .success(updateGraphs);
    };

    $scope.revertOptimization = function () {
      $http.post('/api/analysis/optimization/revert')
        .success(function(){ console.log("OK");});
    };

    // The graphs are shown/hidden after updating the graph type checkboxes.
    $scope.$watch('types', function () {
      if (!cachedResponse || !cachedResponse.graph) return;

      $scope.optimisationGraphs = prepareOptimisationGraphs(cachedResponse.graph);
      $scope.financialGraphs = prepareFinancialGraphs(cachedResponse.graph);
    }, true);

  });
});
