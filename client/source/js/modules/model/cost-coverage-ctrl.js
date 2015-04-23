define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http,
    $state, info, modalService, programsResource, costCoverageHelpers) {

    // In case there is no model data the controller only needs to show the
    // warning that the user should upload a spreadsheet with data.
    if (!info.has_data) {
      $scope.missingModelData = true;
      return;
    }

    var plotTypes, effects, programs;

    var initialize =function () {
      programs = programsResource.data;

      $scope.state = {
        chartsForDataExport: [],
        titlesForChartsExport: [],
        selectionPrograms: info.programs,
        coParams: [],
        hasCostCoverResponse: false,
        selectedProgram: undefined,
        costCoverageChart: undefined
      };

      plotTypes = ['plotdata', 'plotdata_cc', 'plotdata_co'];

      resetGraphs();
    };

    /**
     * Returns the program by name.
     */
    function findProgram (acronym) {
      return _(programs).find(function(entry) {
        return entry.name === acronym;
      });
    }

    var resetGraphs= function () {
      $scope.graphs = {
        plotdata: [],
        plotdata_cc: {},
        plotdata_co: [],
        costOutcomeCharts: [],
        coverageOutcomeCharts: []
      };
    };

    var getlineAreaScatterOptions = function (options, xLabel, yLabel) {
      var defaults = {
        width: 300,
        height: 200,
        margin: {
          top: 20,
          right: 15,
          bottom: 40,
          left: 60
        },
        xAxis: {
          axisLabel: xLabel || 'X'
        },
        yAxis: {
          axisLabel: yLabel || 'Y'
        }
      };

      return _(angular.copy(defaults)).extend(options);
    };

    /* Methods
     ========= */

    /**
     * Calculates graphs objects of types plotdata and plotdata_co
     * returns ready to draw Graph object
     * @param graphData - api reply
     * @returns {{options, data: {lines: Array, scatter: Array}}}
     */
    var setUpPlotdataGraph = function (graphData) {

      var graph = {
        options: getlineAreaScatterOptions({
          linesStyle: ['__color-blue-4', '__color-black __dashed', '__color-black __dashed'],
          title: graphData.title,
          hideTitle: true
        }, graphData.xlabel, graphData.ylabel),
        data: {
          lines: [],
          scatter: []
        }
      };

      // quit if data is empty - empty graph placeholder will be displayed
      if (graphData.ylinedata) {

        var numOfLines = graphData.ylinedata.length;

        _(graphData.xlinedata).each(function (x, index) {
          var y = graphData.ylinedata;
          for (var i = 0; i < numOfLines; i++) {
            if (!graph.data.lines[i]) {
              graph.data.lines[i] = [];
            }

            graph.data.lines[i].push([x, y[i][index]]);
          }
        });
      }

      _(graphData.xscatterdata).each(function (x, index) {
        var y = graphData.yscatterdata;

        if (y[index]) {
          graph.data.scatter.push([x, y[index]]);
        }
      });

      // set up the data limits
      graph.data.limits = [
        [graphData.xlowerlim, graphData.ylowerlim],
        [graphData.xupperlim, graphData.yupperlim]
      ];

      return graph;
    };

    /**
     * Generates ready to plot graph for a cost coverage.
     */
    var prepareCostCoverageGraph = function (data) {
      var graph = {
        options: getlineAreaScatterOptions({
          linesStyle: ['__color-blue-4', '__color-black __dashed', '__color-black __dashed'],
          hideTitle: true
        },
        data.xlabel, data.ylabel),
        data: {
          lines: [],
          scatter: []
        }
      };

      if (data.ylinedata) {
        var numOfLines = data.ylinedata.length;
        _(data.xlinedata).each(function (x, index) {
          var y = data.ylinedata;
          for (var i = 0; i < numOfLines; i++) {
            if (!graph.data.lines[i]) {
              graph.data.lines[i] = [];
            }

            graph.data.lines[i].push([x, y[i][index]]);
          }
        });
      }

      _(data.xscatterdata).each(function (x, index) {
        var y = data.yscatterdata;

        if (y[index]) {
          graph.data.scatter.push([x, y[index]]);
        }
      });

      // set up the data limits
      graph.data.limits = [
        [data.xlowerlim, data.ylowerlim],
        [data.xupperlim, data.yupperlim]
      ];
      return graph;
    };

    /**
     * Receives graphs data with plot type to calculate, calculates all graphs
     * of given type and writes them to $scope.graphs[type] except for the
     * cost coverage graph which will be written to $scope.ccGraph
     *
     * @param data - usually api request with graphs data
     * @param type - string
     */
    var prepareGraphsOfType = function (data, type) {
      if (type === 'plotdata_cc') {
        $scope.ccGraph = prepareCostCoverageGraph(data);
        $scope.ccGraph.options.title = $scope.state.selectedProgram.name;
      } else if (type === 'plotdata' || type === 'plotdata_co') {
        _(data).each(function (graphData) {
          $scope.graphs[type].push(setUpPlotdataGraph(graphData));
        });
      }
    };

    /**
     * Returns the current parameterised plot model.
     */
    var getPlotModel = function() {

      var costCoverageParams = {
        saturation: costCoverageHelpers.convertFromPercent($scope.state.saturationCoverageLevel),
        coveragelower: costCoverageHelpers.convertFromPercent($scope.state.knownMinCoverageLevel),
        coverageupper: costCoverageHelpers.convertFromPercent($scope.state.knownMaxCoverageLevel),
        funding: $scope.state.knownFundingValue,
        scaleup: $scope.state.scaleUpParameter,
        nonhivdalys: $scope.state.nonHivDalys,
        xupperlim: $scope.state.xAxisMaximum,
        cpibaseyear: $scope.state.displayYear,
        perperson: $scope.state.calculatePerPerson
      };

      return {
        progname: $scope.state.selectedProgram.short_name,
        ccparams: costCoverageParams
      };
    };

    /**
     * Returns true if the param is undefined, null or NaN
     */
    var isInvalidParam = function(param) {
      return param === undefined || param === null || typeof param === "number" && isNaN(param);
    };

    /**
     * Returns true if some, but not all of the 4 important cost coverage
     * paramters are filled out.
     */
    $scope.costCoverageFormIsPartlyFilledOut = function () {
      var allRequiredParamsDefined = $scope.state.saturationCoverageLevel &&
                                     $scope.state.knownMinCoverageLevel &&
                                     $scope.state.knownMaxCoverageLevel &&
                                     $scope.state.knownFundingValue;
      var noRequiredParamDefined = isInvalidParam($scope.state.saturationCoverageLevel) &&
                                   isInvalidParam($scope.state.knownMinCoverageLevel) &&
                                   isInvalidParam($scope.state.knownMaxCoverageLevel) &&
                                   isInvalidParam($scope.state.knownFundingValue);

      return !(Boolean(allRequiredParamsDefined) || noRequiredParamDefined);
    };

    /**
     * Returns true if some, but not all of the 4 cost outcome paramters are
     * filled out.
     */
    $scope.costOutcomeFormIsPartlyFilledOut = function (index) {
      var allParamsDefined = $scope.state.coParams[index][0] &&
                             $scope.state.coParams[index][1] &&
                             $scope.state.coParams[index][2] &&
                             $scope.state.coParams[index][3];
      var noParamDefined = isInvalidParam($scope.state.coParams[index][0]) &&
                           isInvalidParam($scope.state.coParams[index][1]) &&
                           isInvalidParam($scope.state.coParams[index][2]) &&
                           isInvalidParam($scope.state.coParams[index][3]);

      return !(Boolean(allParamsDefined) || noParamDefined);
    };

    /**
     * Retrieve and update graphs based on the provided plot models.
     */
    var retrieveAndUpdateGraphs = function (model) {
      $http.post('/api/model/costcoverage', model).success(function (response) {
        effects = response.effectnames;
        $scope.state.coParams = costCoverageHelpers.setUpCoParamsFromEffects(effects);
        $scope.state.hasCostCoverResponse = true;
        $scope.state.costCoverageChart = response.fig_cc;
        $scope.state.coverageOutcomeCharts = response.fig_co;
        $scope.state.costOutcomeCharts = response.fig_cco;

        resetGraphs();
        _(plotTypes).each(function (plotType) {
          prepareGraphsOfType(response[plotType], plotType);
        });
      });
    };

    $scope.changeProgram = function() {
      if($scope.state.hasCostCoverResponse === true) {
        $scope.state.hasCostCoverResponse = false;
      }

      if($scope.state.selectedProgram === null) {
        return null;
      }

      var program = findProgram($scope.state.selectedProgram.short_name);
      $scope.state.saturationCoverageLevel = program.ccparams.saturation ? program.ccparams.saturation * 100 : undefined;
      $scope.state.knownMinCoverageLevel = program.ccparams.coveragelower ? program.ccparams.coveragelower * 100 : undefined;
      $scope.state.knownMaxCoverageLevel = program.ccparams.coverageupper ? program.ccparams.coverageupper * 100 : undefined;
      $scope.state.knownFundingValue = program.ccparams.funding;
      $scope.state.scaleUpParameter = program.ccparams.scaleup;
      $scope.state.nonHivDalys = program.ccparams.nonhivdalys;
      $scope.state.displayYear = program.ccparams.cpibaseyear;
      $scope.state.xAxisMaximum = program.ccparams.xupperlim;
      $scope.state.calculatePerPerson = program.ccparams.perperson;

      var model = getPlotModel();
      retrieveAndUpdateGraphs(model);
    };

    $scope.uploadDefault = function () {
      var message = 'Upload default cost-coverage-outcome curves will be available in a future version of Optima. We are working hard in make it happen for you!';
      modalService.inform(
        function () {},
        'Okay',
        message,
        'Thanks for your interest!'
      );
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets saved in the backend.
     */
    $scope.saveModel = function () {
      if($scope.state.CostCoverageForm.$invalid || $scope.state.CombinedAdjustmentForms.$invalid) {
        modalService.inform(function() {}, 'Ok', 'Please correct all errors on this page before proceeding.', 'Cannot save invalid model');
        return;
      }

      var model = getPlotModel(model);
      model.doSave = true;
      model.all_coparams = costCoverageHelpers.toRequestCoParams($scope.state.coParams);
      model.all_effects = effects;

      var program = findProgram($scope.state.selectedProgram.short_name);
      program.ccparams = model.ccparams;

      retrieveAndUpdateGraphs(model);
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets reverted in the backend.
     */
    $scope.revertModel = function () {
      $scope.changeProgram(); // this will reset the program
      var model = getPlotModel();
      retrieveAndUpdateGraphs(model);
    };

    /**
     * POST /api/model/costcoverage/effect
     *   {
     *     "progname":<chosen progname>
     *     "effect":<effectname for the given row>,
     *     "ccparams":<ccparams>,
     *     "coparams":<coprams from the corresponding coparams block>
     *   }
     */
    $scope.updateCurve = _.debounce(function (graphIndex, AdjustmentForm) {
      if($scope.state.hasCostCoverResponse && AdjustmentForm.$valid && $scope.state.CostCoverageForm.$valid) {
        var model = getPlotModel();
        var coParams = costCoverageHelpers.toRequestCoParams($scope.state.coParams);
        model.coparams = coParams[graphIndex];
        model.effect = effects[graphIndex];

        $http.post('/api/model/costcoverage/effect', model).success(function (response) {
          $scope.graphs.plotdata[graphIndex] = setUpPlotdataGraph(response.plotdata);
          $scope.graphs.plotdata_co[graphIndex] = setUpPlotdataGraph(response.plotdata_co);
          $scope.state.costOutcomeCharts[graphIndex] = response.fig_cco;
          $scope.state.coverageOutcomeCharts[graphIndex] = response.fig_co;
          effects[graphIndex] = response.effect;
        });
      }
    },500);

    /**
     * Collects all existing charts in the $scope.state.chartsForDataExport variable.
     * In addition all titles are gatherd into titlesForChartsExport. This is
     * needed since the cost coverage graphs have no title on the graphs.
     */
    var updateDataForExport = function() {
      $scope.state.chartsForDataExport = [];
      $scope.state.titlesForChartsExport = [];

      if ( $scope.ccGraph) {
        $scope.state.chartsForDataExport.push($scope.ccGraph);
        $scope.state.titlesForChartsExport.push($scope.ccGraph.options.title);
      }

      var charts = _(_.zip($scope.graphs.plotdata, $scope.graphs.plotdata_co)).flatten();
      _( charts ).each(function (chart,index) {
        $scope.state.chartsForDataExport.push(chart);
        $scope.state.titlesForChartsExport.push(chart.options.title);
      });
    };

    $scope.$watch('graphs', updateDataForExport, true);
    $scope.$watch('ccGraph', updateDataForExport, true);

    /**
     * Retrieve and update graphs based on the current plot models only if the
     * graphs are already rendered by pressing the draw button.
     */
    $scope.updateCurves = _.debounce(function() { // debounce a bit so we don't update immediately

      if($scope.state.CostCoverageForm.$valid && $scope.state.hasCostCoverResponse === true) {
        var model = getPlotModel();
        model.all_coparams = costCoverageHelpers.toRequestCoParams($scope.state.coParams);
        model.all_effects = effects;
        retrieveAndUpdateGraphs(model);
      }
    }, 500);

    initialize();

  });


});
