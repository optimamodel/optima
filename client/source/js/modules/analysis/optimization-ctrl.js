/**
 * Honest comment: this controller is doing way too much and this comment will improve once 
 * 'someone' reverse engineers this tech debt and care to do the right thing for a change.
 */

define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('AnalysisOptimizationController', function ($scope, $http,
    $interval, meta, cfpLoadingBar, CONFIG, modalService, typeSelector,
    optimizations, optimizationHelpers) {

      $scope.initialize = function () {
        // angular.op = $scope;
        $scope.$on('$destroy', function () {
          // Make sure that the interval is terminated whe this controller is destroyed
          stopTimer();
        });

        $scope.$watch('state.pieCharts', updateChartsForDataExport, true);
        $scope.$watch('state.outcomeChart', updateChartsForDataExport, true);
        $scope.$watch('state.radarCharts', updateChartsForDataExport, true);
        $scope.$watch('state.optimisationGraphs', updateChartsForDataExport, true);
        $scope.$watch('state.financialGraphs', updateChartsForDataExport, true);
        $scope.$watch('state.stackedBarChart', updateChartsForDataExport, true);
        $scope.$watch('state.multipleBudgetsChart', updateChartsForDataExport, true);
        $scope.$watch('types.plotUncertainties', updateChartsForDataExport, true);
        $scope.$watch('activeTab', $scope.checkExistingOptimization, true);

        $scope.chartsForDataExport = [];
        $scope.meta = meta;
        $scope.types = typeSelector.types;
        $scope.needData = $scope.meta.progs === undefined;
        $scope.activeTab = 1;

        $scope.moneyObjectives = [
          { id: 'inci', title: 'Reduce the annual incidence of HIV' },
          { id: 'incisex', title: 'Reduce the annual incidence of sexually transmitted HIV' },
          { id: 'inciinj', title: 'Reduce the annual incidence of injecting-related HIV' },
          { id: 'mtct', title: 'Reduce annual mother-to-child transmission of HIV' },
          { id: 'mtctbreast', title: 'Reduce annual mother-to-child transmission of HIV among breastfeeding mothers' },
          { id: 'mtctnonbreast', title: 'Reduce annual mother-to-child transmission of HIV among non-breastfeeding mothers' },
          { id: 'deaths', title: 'Reduce annual AIDS-related deaths' },
          { id: 'dalys', title: 'Reduce annual HIV-related DALYs' }
        ];

        $scope.optimizationStatus = statusEnum.NOT_RUNNING;
        $scope.optimizations = [];
        $scope.isDirty = false;

        // According to angular best-practices we should wrap every object/value
        // inside a wrapper object. This is due the fact that directives like ng-if
        // always create a child scope & the reference can get lost.
        // see https://github.com/angular/angular.js/wiki/Understanding-Scopes
        $scope.state = {
          activeOptimizationName: undefined,
          isTestRun: false,
          timelimit: 3600
        };
        resetCharts();

        // Set defaults
        $scope.params = {};

        // Objectives
        $scope.params.objectives = {};
        $scope.params.objectives.what = 'outcome';

        // Outcome objectives defaults
        $scope.params.objectives.outcome = {};
        $scope.params.objectives.outcome.inci = false;
        $scope.params.objectives.outcome.daly = false;
        $scope.params.objectives.outcome.death = false;
        $scope.params.objectives.outcome.costann = false;

        // Default program weightings
        $scope.params.objectives.money = {};
        $scope.params.objectives.money.costs = [];
        if(meta.progs) {
          $scope.programs = meta.progs.long;
          $scope.programCodes = meta.progs.short;

          for ( var i = 0; i < meta.progs.short.length; i++ ) {
            $scope.params.objectives.money.costs[i] = 100;
          }

          // Constraints Defaults
          $scope.params.constraints = {};
          $scope.params.constraints.txelig = 1;
          $scope.params.constraints.dontstopart = true;

          $scope.params.constraints.yeardecrease = [];
          $scope.params.constraints.yearincrease = [];
          $scope.params.constraints.totaldecrease = [];
          $scope.params.constraints.totalincrease = [];
          $scope.params.constraints.coverage = [];

          // Initialize program constraints models
          for ( var i = 0; i < meta.progs.short.length; i++ ) {
            $scope.params.constraints.yeardecrease[i] = {};
            $scope.params.constraints.yeardecrease[i].use = false;
            $scope.params.constraints.yeardecrease[i].by = 100;

            $scope.params.constraints.yearincrease[i] = {};
            $scope.params.constraints.yearincrease[i].use = false;
            $scope.params.constraints.yearincrease[i].by = 100;

            $scope.params.constraints.totaldecrease[i] = {};
            $scope.params.constraints.totaldecrease[i].use = false;
            $scope.params.constraints.totaldecrease[i].by = 100;

            $scope.params.constraints.totalincrease[i] = {};
            $scope.params.constraints.totalincrease[i].use = false;
            $scope.params.constraints.totalincrease[i].by = 100;

            $scope.params.constraints.coverage[i] = {};
            $scope.params.constraints.coverage[i].use = false;
            $scope.params.constraints.coverage[i].level = 0;
            $scope.params.constraints.coverage[i].year = undefined;
          }
        };

        $scope.validations = {
          fixedBudget: {
            valid: function () { return $scope.params.objectives.outcome.fixed !== undefined; },
            message: 'Please enter a value for the fixed budget.',
            condition: function () { return $scope.params.objectives.funding === 'constant'; }
          },
          variableBudget: {
            valid: function () { return validateVariableBudgets()},
            message: "Please enter a budget for each year.",
            condition: function () { return $scope.params.objectives.funding === 'variable'; }
          },
          budgetType: {
            valid: function () { return $scope.params.objectives.funding!==undefined; },
            message: "Please pick at least one budget type."
          },
          objectivesToMinimizeCount: {
            valid: function () { return validateObjectivesToMinimize().valid; },
            message: "You must pick at least one objective to minimize."
          },
          objectivesOutcomeWeights: {
            valid: function () {return validateOutcomeWeights().valid; },
            message: "You must specify the weighting parameters for all objectives to minimize."
          }
        };

        $scope.objectivesToMinimize = [
          {
            name:"Cumulative new HIV infections",
            slug:"inci",
            title: "New infections weighting"
          },
          {
            name:"Cumulative DALYs",
            slug: "daly",
            title:"DALYs weighting"
          },
          {
            name:" Cumulative AIDS-related deaths",
            slug:"death",
            title:"Deaths weighting"
          },
          {
            name:"Total HIV-related costs",
            slug:"cost",
            title:"Costs weighting"
          }
        ];

        // $scope.validateYears = validateYears;
        $scope.validateVariableBudgets = validateVariableBudgets;
        $scope.validateObjectivesToMinimize = validateObjectivesToMinimize;
        $scope.validateOutcomeWeights = validateOutcomeWeights;

        // The graphs are shown/hidden after updating the graph type checkboxes.
        $scope.$watch('types', drawGraphs, true);
        $scope.yearLoop = [];
        $scope.yearCols = [];

        // apply existing optimization data, if present
        if (optimizations && optimizations.data) {
          $scope.initOptimizations(optimizations.data.optimizations, undefined, true);
        }

    };

    var errorMessages = [];

    var statusEnum = {
      NOT_RUNNING: { text: "", isActive: false, checking: false },
      RUNNING: { text: "Optimization is running", isActive: true, checking: false },
      REQUESTED_TO_STOP : { text:"Optimization is requested to stop", isActive: true, checking: false },
      STOPPING : { text:"Optimization is stopping", isActive: true, checking: false },
      CHECKING: {text:"Checking for existing optimization", isActive: false, checking: true}
    };

    /**
     * Empty charts
     */
    var resetCharts = function () {
      $scope.state.optimisationGraphs = [];
      $scope.state.financialGraphs = [];
      $scope.state.radarCharts = [];
      $scope.state.pieCharts = [];
      $scope.state.stackedBarChart = undefined;
      $scope.state.outcomeChart = undefined;
    };

    var optimizationTimer;

    var linesGraphOptions = {
      height: 200,
      width: 320,
      margin: CONFIG.GRAPH_MARGINS,
      xAxis: {
        axisLabel: 'Year'
      },
      yAxis: {
        axisLabel: ''
      }
    };

    /*
    * Returns an graph based on the provided yData.
    *
    * yData should be an array where each entry contains an array of all
    * y-values from one line.
    */
    var generateGraph = function (yData, xData, title, legend, xLabel, yLabel) {
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
        graph.data.lines.push(_.zip(xData, lineData));
      });

      return graph;
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generatePieChart = function (data, legend) {
      var graphData = [];

      var options = {
        height: 350,
        width: 350,
        margin: {
          top: 20,
          right: 100,
          bottom: 20,
          left: 100
        },
        title: data.name
      };

      graphData = _(data).map( function (value, index) {
        return { value: value, label: legend[index] };
      });

      return {
        'data': {slices: graphData},
        'options': options
      };
    };

    /**
     * Returns all pie charts.
     */
    var preparePieCharts = function (data) {

      var charts = [];

      if (data[0] && data[0].piedata) {
        charts.push(generatePieChart(data[0].piedata, data[0].legend));
      }

      if (data[1] && data[1].piedata) {
        charts.push(generatePieChart(data[1].piedata, data[0].legend)); // not set for data[1]
      }

      return charts;
    };

    /**
     * Returns a prepared chart object for a radar chart.
     */
    var generateRadarChart = function (data, legend) {
      var graphData = [{axes: []}, {axes: []}, {axes: []}];

      var options = {
        legend: [],
        title: data.name
      };

      graphData[0].axes = _(data.low).map( function (value, index) {
        return { value: value, axis: legend[index] };
      });
      graphData[1].axes = _(data.best).map( function (value, index) {
        return { value: value, axis: legend[index] };
      });
      graphData[2].axes = _(data.high).map( function (value, index) {
        return { value: value, axis: legend[index] };
      });

      return {
        'data': graphData,
        'options': options,
        'radarAxesName': 'Programs'
      };
    };

    /**
     * Returns all radar charts.
     */
    var prepareRadarCharts = function (data) {

      var charts = [];

      if (data[0] && data[0].radardata) {
        charts.push(generateRadarChart(data[0].radardata, data[0].legend));
      }

      if (data[1] && data[1].radardata) {
        charts.push(generateRadarChart(data[1].radardata, data[0].legend)); // not set for data[1]
      }

      return charts;
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generateStackedBarChart = function (yData, xData, legend, title) {
      var graphData = [];

      var options = {
        height: 200,
        width: 700,
        margin: CONFIG.GRAPH_MARGINS,
        xAxis: {
          axisLabel: 'Year'
        },
        yAxis: {
          axisLabel: ''
        },
        legend: legend,
        title: title
      };


      graphData = _(xData).map( function (xValue, index) {
        var yValues = _(yData).map( function (yEntry) { return yEntry[index]; } );
        return [xValue, yValues];
      });

      return {
        'data': {bars: graphData},
        'options': options
      };
    };

    /**
     * Returns a stacked bar chart.
     */
    var prepareStackedBarChart = function (data) {
      return generateStackedBarChart(data.stackdata, data.xdata, data.legend,
        data.title);
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generateMultipleBudgetsChart = function (yData, xData, labels, legend,
        title, leftTitle, rightTitle) {
      var graphData = [];

      var options = {
        height: 200,
        width: 700,
        margin: CONFIG.GRAPH_MARGINS,
        xAxis: {
          axisLabel: ''
        },
        yAxis: {
          axisLabel: 'Spent'
        },
        legend: legend,
        title: title,
        leftTitle: leftTitle,
        rightTitle: rightTitle
      };

      graphData = _(xData).map( function (xValue, index) {
        return [labels[index], xValue, yData[index]];
      });

      return {
        'data': {bars: graphData},
        'options': options
      };
    };

    /**
     * Returns a stacked bar chart.
     */
    var prepareMultipleBudgetsChart = function (data, outcomeData) {
      return generateMultipleBudgetsChart(data.bardata, outcomeData.bardata,
        data.xlabels, data.legend, data.title, outcomeData.title, data.ylabel);
      };

    /**
     * Regenerate graphs based on the results and type settings in the UI.
     */
    var prepareOptimisationGraphs = function (results) {
      var graphs = [];

      if (!results) {
        return graphs;
      }

      _($scope.types.population).each( function (type) {

        if (type === undefined) return;
        var data = results[type.id];
        if (data !== undefined) {

          // generate graphs showing the overall data for this type
          if (type.total) {
            var graph = generateGraph(
              data.tot.data, results.tvec,
              data.tot.title, data.tot.legend,
              data.xlabel, data.tot.ylabel
            );
            graphs.push(graph);
          }

          // generate graphs for this type for each population
          if (type.byPopulation) {
            _(data.pops).each( function (population) {
              var graph = generateGraph(
                population.data, results.tvec,
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
    var generateFinancialGraph = function (data) {
      var graph = generateGraph(data.data, data.xdata, data.title, data.legend, data.xlabel, data.ylabel);
      return graph;
    };

    var prepareFinancialGraphs = function (graphData) {
      var graphs = [];

      if (graphData === undefined) return graphs;

      // annual cost charts
      _(['existing', 'future', 'total']).each( function (type) {
        var chartData = graphData.costann[type][$scope.types.activeAnnualCost];
        var isActive = $scope.types.costs[0][type];
        if (chartData && isActive) {
          graphs.push(generateFinancialGraph(chartData));
        }
      });


      // cumulative cost charts
      _(['existing', 'future', 'total']).each( function (type) {
        var chartData = graphData.costcum[type];
        var isActive = $scope.types.costs[1][type];
        if (chartData && isActive) {
          graphs.push(generateFinancialGraph(chartData));
        }
      });

      // commitments
      var commitChartData = graphData.commit[$scope.types.activeAnnualCost];
      var commitIsActive = $scope.types.costs[2].checked;
      if (commitChartData && commitIsActive) {
        graphs.push(generateFinancialGraph(commitChartData));
      }

      return graphs;
    };

    var prepareOutcomeChart = function (data) {
      if (data === undefined) return undefined;

      var chart = {
        options: angular.copy(linesGraphOptions),
        data: {
          lines: [],
          scatter: []
        }
      };
      chart.options.height = 320;
      chart.options.margin.bottom = 165;

      chart.options.title = data.title;
      chart.options.xAxis.axisLabel = data.xlabel;
      chart.options.yAxis.axisLabel = data.ylabel;
      chart.data.lines.push(_.zip(data.xdata, data.ydata));
      return chart;
    };

    $scope.optimizationByName = function (name) {
      return _($scope.optimizations).find( function (item) {
        return item.name == name;
      });
    };

    // makes all graphs to recalculate and redraw
    function drawGraphs () {
      var optimization = $scope.optimizationByName($scope.state.activeOptimizationName);

      if (!optimization || !optimization.result || !optimization.result.plot) return;

      var data = optimization.result.plot[0];
      resetCharts();
      if (data.alloc instanceof Array) {
        $scope.state.pieCharts = preparePieCharts(data.alloc);
        $scope.state.radarCharts = prepareRadarCharts(data.alloc);
        $scope.state.outcomeChart = prepareOutcomeChart(data.outcome);
      } else {
        if (data.alloc.bardata) {
          $scope.state.multipleBudgetsChart = prepareMultipleBudgetsChart(data.alloc,
            data.outcome);
        } else if (data.alloc.stackdata) {
          $scope.state.stackedBarChart = prepareStackedBarChart(data.alloc);
          $scope.state.outcomeChart = prepareOutcomeChart(data.outcome);
        }
      }
      $scope.state.optimisationGraphs = prepareOptimisationGraphs(data.multi);
      $scope.state.financialGraphs = prepareFinancialGraphs(data.multi);
    }

    // makes all graphs to recalculate and redraw
    function updateGraphs (data) {
      /* new structure keeps everything together:
       * data.plot[n].alloc => pie & radar
       * data.plot[n].multi => old line-scatterplots
       * data.plot[n].outcome => new line plot
       * n - sequence number of saved optimization
       */
      if (data && data.plot && data.plot.length > 0) {
        var optimization = $scope.optimizationByName($scope.state.activeOptimizationName);
        optimization.result = data;
        typeSelector.enableAnnualCostOptions($scope.types, data.plot[0].multi);
        drawGraphs();
      }
    };

    /* If some of the budgets are undefined, return false */
    function validateVariableBudgets () {
      return _(_($scope.params.objectives.outcome.variable).toArray()).some( function (budget) {return budget === undefined;}) === false;
    }

    // function validateYears () {
    //    if($scope.params.objectives.year!==undefined){
    //      var start = parseInt($scope.params.objectives.year.start);
    //      var end = parseInt($scope.params.objectives.year.end);
    //      var until = parseInt($scope.params.objectives.year.until);
    //      return {
    //       start:start,
    //       end: end,
    //       until: until,
    //       valid: (isNaN(start) ||  isNaN(end) || isNaN(until) || end <= start || until <= start) === false
    //     };
    //    }
    //    return {
    //     valid:false
    //   };
    // };

    function validateObjectivesToMinimize () {
      var checkedPrograms = _($scope.objectivesToMinimize).filter( function (a) {
        return $scope.params.objectives.outcome[a.slug] === true;
      });
      return {
        checkedPrograms : checkedPrograms,
        valid: checkedPrograms.length > 0
      };
    }

    function validateOutcomeWeights () {
      var checkedPrograms = _($scope.objectivesToMinimize).filter( function (a) {
        return $scope.params.objectives.outcome[a.slug] === true &&
          !($scope.params.objectives.outcome[a.slug+'weight']!==undefined &&
          $scope.params.objectives.outcome[a.slug+'weight']>0);
      });
      return {
        checkedPrograms : checkedPrograms,
        valid: checkedPrograms.length === 0
      };
    }

    /**
    * Evaluates the conditions defined in $scope.validations and when there is one that do not pass, 
    * it adds its message with feedback for the user to the errorMessages array.
    */
    function checkValidation () {
      errorMessages = [];
      _($scope.validations).each( function (validation) {
        if(validation.valid()!==true && (validation.condition === undefined || validation.condition() === true)){
          errorMessages.push({message:validation.message});
        }
      });
    };

    /**
     * Returns true if the requisites to view the results are met.
     */
    $scope.canViewResults = function () {
      return $scope.canViewResults;
    };

    /**
     * Returns true if the requisites to view the results are NOT met.
     */
    $scope.isPreventingViewResults = function () {
      return !$scope.canViewResults;
    };

    /**
     * Returns true if at least one chart is available
     */
    $scope.someGraphAvailable = function () {
      return !(_.isEmpty($scope.state.radarCharts)) ||
        !(_.isEmpty($scope.state.optimisationGraphs)) ||
        !(_.isEmpty($scope.state.financialGraphs)) ||
        !(_.isEmpty($scope.state.pieCharts)) ||
        $scope.state.stackedBarChart !== undefined ||
        $scope.state.outcomeChart !== undefined;
    };

    /**
     * If the string is undefined return empty, otherwise just return the string
     * @param str
     * @returns {string}
     */
    function strOrEmpty (str){
      return _(str).isUndefined() ? '' : str;
    }

    /**
     * Join the word with a comma between them, except for the last word
     * @param arr
     * @param prop if it's not undefined it will pick that specific property from the object
     * @param quote should the sentence be quoted or not
     * @param before add something before each word
     * @param after add something after each word
     * @returns {string}
     */
    function joinArrayAsSentence (arr, prop, quote, before, after){
      quote = quote ? '"':'';
      before = strOrEmpty(before);
      after = strOrEmpty(after);
      return quote + _.compact(_(arr).map( function (val) {var p = (prop ? val[prop] : val);return p ? (before + strOrEmpty(p) + after ) : undefined;})).join(", ") + quote;
    }

    function constructOptimizationMessage () {
      var budgetLevel;
      var checkedPrograms = joinArrayAsSentence(validateObjectivesToMinimize().checkedPrograms, 'name', true);
      var startYear = $scope.params.objectives.year.start;
      var endYear = $scope.params.objectives.year.end;

      if ($scope.params.objectives.funding === 'variable') {
        budgetLevel = " budget level " + joinArrayAsSentence(_.compact(_($scope.params.objectives.outcome.variable).toArray()), undefined, false, "$");
      } else if ($scope.params.objectives.funding === 'constant') {
        budgetLevel = " fixed budget of $" + $scope.params.objectives.outcome.fixed + " per year";
      } else if ($scope.params.objectives.funding === 'range') {
        budgetLevel = " budget range between $" + $scope.params.objectives.outcome.budgetrange.minval;
        budgetLevel = budgetLevel + " to $" + $scope.params.objectives.outcome.budgetrange.maxval;
      }

      if ( budgetLevel && checkedPrograms && startYear && endYear ) {
        $scope.showOptimizationMessage = true;

        $scope.optimizationMessage = {
          checkedPrograms: checkedPrograms,
          startYear: startYear,
          endYear: endYear,
          budgetLevel: budgetLevel
        };
      }
    }

    $scope.setActiveTab = function (tabNum){
      // if(tabNum === 3){
      // /*Prevent going to third tab if something is invalid in the first tab.
      //   Cannot just use $scope.state.OptimizationForm.$invalid for this because the validation of the years and the budgets is done in a different way. */
      //   checkValidation();
      //   if(errorMessages.length > 0){
      //     modalService.informError(errorMessages, 'Cannot view results');
      //     return;
      //   }
      //   if ($scope.state.OptimizationForm.$invalid) {
      //     modalService.inform( function () {}, 'Ok', 'Please correct all errors on this page before proceeding.', 'Cannot view results' );
      //     return;
      //   }
      //   constructOptimizationMessage();
      // }
      $scope.activeTab = tabNum;
    };

    $scope.initTimer = function (status) {
      if ( !angular.isDefined( optimizationTimer ) ) {
        // Keep polling for updated values after every 5 seconds till we get an error.
        // Error indicates that the model is not optimizing anymore.
        optimizationTimer = $interval(checkWorkingOptimization, 30000, 0, false);
        $scope.optimizationStatus = status;
        $scope.errorText = '';
        // start cfpLoadingBar loading
        // calculate the number of ticks in timelimit
        var val = ($scope.state.timelimit * 1000) / 250;
        // callback function in start to be called in place of _inc()
        cfpLoadingBar.start( function () {
          if (cfpLoadingBar.status() >= 0.95) {
            return;
          }
          var pct = cfpLoadingBar.status() + (0.95/val);
          cfpLoadingBar.set(pct);
        });
      }
    };

    $scope.startOptimization = function () {
      var params = optimizationHelpers.toRequestParameters($scope.params, $scope.state.activeOptimizationName, $scope.state.timelimit);
      $http.post('/api/analysis/optimization/start', params, {ignoreLoadingBar: true})
        .success( function (data, status, headers, config) {
          if (data.status == "OK" && data.join) {
            $scope.initTimer(statusEnum.RUNNING);
          } else {
            console.log("Cannot poll for optimization now");
          }
        });
    };

    $scope.checkExistingOptimization = function (newTab, oldTab) {
      if(newTab !=3) {
        stopTimer();
      } else {
        checkWorkingOptimization();
      }
    };

    function checkWorkingOptimization() {
      $http.get('/api/analysis/optimization/working', {ignoreLoadingBar: true})
        .success( function (data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          } else {
            if (data.status == 'Running') $scope.optimizationStatus = statusEnum.RUNNING;
            if (data.status == 'Stopping') $scope.optimizationStatus = statusEnum.STOPPING;
            $scope.initTimer($scope.optimizationStatus);
          }
          $scope.isDirty = data.dirty;
          $scope.initOptimizations(data.optimizations, $scope.state.activeOptimizationName);
        })
        .error( function (data, status, headers, config) {
          if (data && data.exception) {
            $scope.errorText = data.exception;
          }
          stopTimer();
        });
    }

    $scope.stopOptimization = function () {
      modalService.confirm(
        function (){
          $http.get('/api/analysis/optimization/stop')
          .success( function (data) {
            // Do not cancel timer yet, if the optimization is running
            if ($scope.optimizationStatus) {
              $scope.optimizationStatus = statusEnum.REQUESTED_TO_STOP;
            }
          });
        },
        function (){},
        'Yes, Stop Optimization',
        'No',
        'Warning, optimization has not converged. Results cannot be used for analysis.',
        'Warning!'
      );
    };

    function stopTimer() {
      if ( angular.isDefined( optimizationTimer ) ) {
        $interval.cancel(optimizationTimer);
        optimizationTimer = undefined;
        $scope.optimizationStatus = statusEnum.NOT_RUNNING;
        cfpLoadingBar.complete();
      }
    }

    $scope.deleteOptimization = function (optimizationName) {
      $http.post('/api/analysis/optimization/remove/' + optimizationName)
        .success( function (data){
          $scope.initOptimizations(data.optimizations, undefined);
        });
    };

    $scope.saveOptimization = function () {
      $http.post('/api/analysis/optimization/save')
        .success( function (data) {
          $scope.isDirty = false;
          $scope.initOptimizations(data.optimizations, $scope.state.activeOptimizationName);
      });
    };


    $scope.revertOptimization = function () {
      $http.post('/api/analysis/optimization/revert')
        .success( function (data) {
          $scope.isDirty = false;
          $scope.initOptimizations(data.optimizations, $scope.state.activeOptimizationName);
      });
    };

    $scope.addOptimization = function () {
      var create = function (name) {
        var url = '/api/analysis/optimization/create';
        var params = optimizationHelpers.toRequestParameters($scope.params, name);
        $http.post(url, params).success( function (data) {
          $scope.initOptimizations(data.optimizations, name);
        });
      };

      modalService.addOptimization( function (name) { create(name); }, $scope.optimizations );
    };

    /**
     * Returns true if the start & end year are required.
     */
    $scope.yearsAreRequired = function () {
      if (!$scope.params.objectives.funding || $scope.params.objectives.funding !== 'variable') {
        return false;
      }
      if (!$scope.params.objectives.year ||
          !$scope.params.objectives.year.start ||
          !$scope.params.objectives.year.end){
        return true;
      }
      return false;
    };

    /**
     * Update the variables depending on the range in years.
     */
    $scope.updateYearRange = function () {

      // only for variable funding the year range is relevant to produce the loop & col
      if ( !$scope.params.objectives.funding || $scope.params.objectives.funding !== 'variable') {
        return;
      }

      // reset data
      $scope.params.objectives.outcome.variable = {};
      $scope.yearLoop = [];
      $scope.yearCols = [];

      // parse years
      if ($scope.params.objectives.year === undefined) {
        return;
      }
      var start = parseInt($scope.params.objectives.year.start);
      var end = parseInt($scope.params.objectives.year.end);
      if ( isNaN(start) ||  isNaN(end) || end <= start) {
        return;
      }

      // initialize data
      var years = _.range(start, end + 1);
      $scope.yearLoop = _(years).map( function (year) { return { year: year}; } );

      var cols = 5;
      var rows = Math.ceil($scope.yearLoop.length / cols);
      $scope.yearCols = _(_.range(0, rows)).map( function (col, index) {
        return {start: index*cols, end: (index*cols)+cols };
      });

    };

    /**
     * Collects all existing charts in the $scope.chartsForDataExport variable.
     */
    var updateChartsForDataExport = function () {
      $scope.chartsForDataExport = [];

      if ( $scope.state.pieCharts && !$scope.types.plotUncertainties ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.pieCharts);
      }

      if ( $scope.state.radarCharts && $scope.types.plotUncertainties ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.radarCharts);
      }

      if ( $scope.state.stackedBarChart ) {
        $scope.chartsForDataExport.push($scope.state.stackedBarChart);
      }

      if ( $scope.state.outcomeChart ) {
        $scope.chartsForDataExport.push($scope.state.outcomeChart);
      }

      if ( $scope.state.multipleBudgetsChart ) {
        $scope.chartsForDataExport.push($scope.state.multipleBudgetsChart);
      }

      if ( $scope.state.optimisationGraphs ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.optimisationGraphs);
      }

      if ( $scope.state.financialGraphs ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.financialGraphs);
      }

    };

    /**
     * Changes active constrains and objectives to the values in provided optimization
     * @param optimization {Object}
     */
    $scope.applyOptimization = function (name, overwriteParams) {
      var optimization = $scope.optimizationByName(name);
      if (overwriteParams) {
        var objectives = optimizationHelpers.toScopeObjectives(optimization.objectives);
        _.extend($scope.params.objectives, objectives);
        _.extend($scope.params.constraints, optimization.constraints);
      }
      if (optimization.result) {
        updateGraphs(optimization.result);
      } else {
        resetCharts();
        typeSelector.resetAnnualCostOptions($scope.types);
      }
      constructOptimizationMessage();
    };

    // apply default optimization on page load
    $scope.initOptimizations = function (optimizations, name, overwriteParams) {
      if (!optimizations) return;

      $scope.optimizations = angular.copy(optimizations);

      var nameExists = name && _($scope.optimizations).some( function (item) {
        return item.name == name;
      });

      if (nameExists) {
        $scope.state.activeOptimizationName = name;
      } else {
        $scope.state.activeOptimizationName = undefined;
        var optimization = _($scope.optimizations).first();
        if (optimization) {
          $scope.state.activeOptimizationName = optimization.name;
        }
      }

      $scope.applyOptimization($scope.state.activeOptimizationName, overwriteParams);
    };

    $scope.updateTimelimit = function () {
      if ($scope.state.isTestRun) {
        $scope.state.timelimit = 60;
      } else {
        $scope.state.timelimit = 3600;
      }
    };

    $scope.initialize();
  });
});
