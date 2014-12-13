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

    $scope.lineStyles = ['__blue', '__green', '__red', '__orange',
      '__violet', '__black', '__light-orange', '__light-green'];

    var linesGraphOptions = {
      height: 200,
      width: 320,
      margin: {
        top: 20,
        right: 10,
        bottom: 45,
        left: 70
      },
      linesStyle: $scope.lineStyles,
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
    var generateGraph = function(yData, xData, title) {
      var linesGraphData = {
        lines: [],
        scatter: []
      };

      var graph = {
        options: angular.copy(linesGraphOptions),
        data: angular.copy(linesGraphData),
        title: title
      };

      _(yData).each(function(lineData) {
        graph.data.lines.push(generateLineData(xData, lineData));
      });

      return graph;
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
            var title = data.tot.title;
            var graph = generateGraph(data.tot.data, response.tvec, title);
            graph.options.xAxis.axisLabel = data.xlabel;
            graph.options.yAxis.axisLabel = data.tot.ylabel;
            graph.legend = data.tot.legend;
            graphs.push(graph);
          }

          // generate graphs for this type for each population
          if (type.byPopulation) {
            _(data.pops).each(function (population, populationIndex) {

              var title = population.title;
              var graph = generateGraph(population.data, response.tvec, title);
              graph.options.xAxis.axisLabel = data.xlabel;
              graph.options.yAxis.axisLabel = population.ylabel;
              graph.legend = population.legend;
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
      var graph = generateGraph(data.data, data.xdata, data.title);

      graph.options.xAxis.axisLabel = data.xlabel;
      graph.options.yAxis.axisLabel = data.ylabel;
      graph.options.linesStyle = ['__black', '__black', '__black',
        '__black', '__black', '__black', '__black', '__black'];
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

    // The graphs are shown/hidden after updating the graph type checkboxes.
    $scope.$watch('types', function () {
      if (!cachedResponse || !cachedResponse.graph) return;

      $scope.optimisationGraphs = prepareOptimisationGraphs(cachedResponse.graph);
      $scope.financialGraphs = prepareFinancialGraphs(cachedResponse.graph);
    }, true);

  });
});
