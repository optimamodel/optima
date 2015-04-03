define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http,
    $state, info, modalService, programs) {

    var plotTypes, effectNames;

    var initialize =function () {
      $scope.chartsForDataExport = [];
      $scope.titlesForChartsExport = [];

      // show message "calibrate the model" and disable the form elements
      $scope.needData = !info.has_data;
      $scope.cannotCalibrate = !info.can_calibrate;
      $scope.notReady = $scope.needData || $scope.cannotCalibrate;

      $scope.optionsErrorMessage = 'To define a cost-coverage curve, values must be provided in the first three text boxes.';
      $scope.needAllCCParamsMessage = 'First four text boxes must be either all empty, or all have values in them.';
      $scope.all_programs = programs.data;

      if ( !$scope.needData ) {
        $scope.selectionPrograms = initializePrograms(info.programs, $scope.all_programs);
        $scope.selectedProgram = $scope.selectionPrograms[0];
        $scope.displayedProgram = null;

        $scope.coParams = [];

        $scope.hasCostCoverResponse = false;
      }

      plotTypes = ['plotdata', 'plotdata_cc', 'plotdata_co'];

      resetGraphs();
    };

    function findProgram (acronym) {
      return _($scope.all_programs).find(function(entry) {
        return entry.name === acronym;
      });
    }

    /**
     * Redirects the user to View & Calibrate screen.
     */
    $scope.gotoViewCalibrate = function() {
      $state.go('model.view');
    };

    /**
    * Creates the models of the programs for this controller.
    * If the backend do not present values for the categories, we'll use 'Others' as default.
    */
    function initializePrograms (programsWithNames, programsWithParams) {
      // TODO I blieve this is only here to ensure the correct order
      var programs =  _(programsWithNames).map(function (item) {
        var acronym = item.short_name;

        var program = _(programsWithParams).find(function(entry) {
          return entry.name === acronym;
        });

        return {
          name: item.name,
          acronym: acronym,
          category: item.category
        };
      });
      programs.unshift({name:'-- No program selected --',category:null, acronym:null});
      return programs;
    }

    var resetGraphs= function () {
      $scope.graphs = {
        plotdata: [],
        plotdata_cc: {},
        plotdata_co: []
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
        $scope.ccGraph.options.title = $scope.displayedProgram.name;
      } else if (type === 'plotdata' || type === 'plotdata_co') {
        _(data).each(function (graphData) {
          $scope.graphs[type].push(setUpPlotdataGraph(graphData));
        });
      }
    };

    var setUpCOParamsFromEffects = function (effectNames) {
      $scope.coParams = _(effectNames).map(function (effect) {
        return [
          (effect[2] && effect[2][0])? effect[2][0] * 100 : null,
          (effect[2] && effect[2][1])? effect[2][1] * 100 : null,
          (effect[2] && effect[2][2])? effect[2][2] * 100 : null,
          (effect[2] && effect[2][3])? effect[2][3] * 100 : null
        ];
      });
    };

    $scope.convertFromPercent = function (value) {
      if (typeof value !== "number" || isNaN(value)) {
        return NaN;
      }
      return value / 100;
    };

    $scope.convertedCoParams = function () {
      return _($scope.coParams).map(function (effect) {
        return [
          $scope.convertFromPercent(effect[0]),
          $scope.convertFromPercent(effect[1]),
          $scope.convertFromPercent(effect[2]),
          $scope.convertFromPercent(effect[3])
        ];
      });
    };

    /**
     * Converts settings from the scope to costCoverage params
     */
    $scope.costCoverageParams = function () {
      return {
        saturation: $scope.convertFromPercent($scope.saturationCoverageLevel),
        coveragelower: $scope.convertFromPercent($scope.knownMinCoverageLevel),
        coverageupper: $scope.convertFromPercent($scope.knownMaxCoverageLevel),
        funding: $scope.knownFundingValue,
        scaleup: $scope.scaleUpParameter,
        nonhivdalys: $scope.nonHivDalys,
        xupperlim: $scope.xAxisMaximum,
        cpibaseyear: $scope.displayYear,
        perperson: $scope.calculatePerPerson
      };
    };

    /**
     * Returns the current parameterised plot model.
     */
    var getPlotModel = function() {
      return {
        progname: $scope.selectedProgram.acronym,
        ccparams: $scope.costCoverageParams(),
        coparams: []
      };
    };

    /**
     * Returns true if all of the elements in an array are defined or not null
     */
    var hasAllElements = function(params) {
      return params && params.length && _(params).every(function(item) { return item; });
    };

    /**?
     * TODO remove?
     * Returns true if all of the elements in an array are undefined, null or NaN
     */
    var hasOnlyInvalidEntries = function(params) {
      return params.every(function(item) {
        return item === undefined || item === null || typeof item === "number" && isNaN(item);
      });
    };

    /**
     * Returns true if the param is undefined, null or NaN
     */
    var isInvalidParam = function(param) {
      return param === undefined || param === null || typeof param === "number" && isNaN(param);
    };

    function areValidCoParams (params) {
      return hasAllElements(params) || hasOnlyInvalidEntries(params);
    }

    $scope.hasValidCCParams = function () {
      var params = $scope.costCoverageParams();
      var allRequiredParamsDefined = params.saturation && params.coveragelower && params.coverageupper && params.funding;
      var noRequiredParamDefined = isInvalidParam(params.saturation) && isInvalidParam(params.coveragelower) && isInvalidParam(params.coverageupper) && isInvalidParam(params.funding);

      return (allRequiredParamsDefined || noRequiredParamDefined);
    };

    $scope.hasAllCCParams = function() {
      return true;
      // return hasAllElements($scope.costCoverageParams().slice(0, 4));
    };

    /**
     * Update current program ccparams based on the selected program.
     *
     * This function is supposed to be called before Draw / Redraw / Save.
     */
    var updateCCParams = function(model) {
      if (model.ccparams) {
        var program = findProgram($scope.selectedProgram.acronym);
        program.ccparams = model.ccparams;
      }
    };

    /**
     * Retrieve and update graphs based on the provided plot models.
     */
    var retrieveAndUpdateGraphs = function (model) {
      // validation on Cost-coverage curve plotting options
      if (!$scope.hasValidCCParams(model.ccparams)){
        return;
      }

      // stop further execution and return in case of null selectedProgram
      if ( $scope.selectedProgram.acronym === null ) {
        return;
      }

      // clean up model by removing unnecessary parameters
      // if (_.isEmpty(model.ccparams) || hasOnlyInvalidEntries(model.ccparams.slice(0,3))) {
      //   delete model.ccparams;
      // }

      if (_.isEmpty(model.coparams) || hasOnlyInvalidEntries(model.coparams)) {
        delete model.coparams;
      }

      // update current program ccparams,if applicable
      updateCCParams(model);

      $http.post('/api/model/costcoverage', model).success(function (response) {
        if (response.status === 'OK') {

          $scope.displayedProgram = angular.copy($scope.selectedProgram);
          effectNames = response.effectnames;
          setUpCOParamsFromEffects(response.effectnames);
          $scope.hasCostCoverResponse = true;

          resetGraphs();
          _(plotTypes).each(function (plotType) {
            prepareGraphsOfType(response[plotType], plotType);
          });
        }
      });
    };

    $scope.changeProgram = function() {

      if($scope.hasCostCoverResponse === true) {
        $scope.hasCostCoverResponse = false;
      }

      var program = findProgram($scope.selectedProgram.acronym);
      $scope.saturationCoverageLevel = program.ccparams.saturation;
      $scope.knownMinCoverageLevel = program.ccparams.coveragelower;
      $scope.knownMaxCoverageLevel = program.ccparams.coverageupper;
      $scope.knownFundingValue = program.ccparams.funding;
      $scope.scaleUpParameter = program.ccparams.scaleup;
      $scope.nonHivDalys = program.ccparams.nonhivdalys;
      $scope.displayYear = program.ccparams.cpibaseyear;
      $scope.xAxisMaximum = program.ccparams.xupperlim;
      $scope.calculatePerPerson = program.ccparams.perperson;

      $scope.generateCurves();
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     */
    $scope.generateCurves = function () {
      var model = getPlotModel();
      if ($scope.hasCostCoverResponse) {
        model.all_coparams = $scope.convertedCoParams();
        model.all_effects = effectNames;
      }

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
      var model = getPlotModel(model);
      model.doSave = true;
      model.all_coparams = $scope.convertedCoParams();
      model.all_effects = effectNames;
      retrieveAndUpdateGraphs(model);
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets reverted in the backend.
     */
    $scope.revertModel = function () {
      var model = getPlotModel(model);
      model.doRevert = true;
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
      if(!$scope.hasCostCoverResponse && AdjustmentForm.$valid && $scope.CostCoverageForm.$valid && $scope.hasValidCCParams()) {
        var model = getPlotModel();
        model.coparams = $scope.convertedCoParams()[graphIndex];
        model.effect = effectNames[graphIndex];
        if (!areValidCoParams(model.coparams)) {
          // no need to show dialog - we inform the user with hints
          return;
        }

        // clean up model by removing unnecessary parameters
        if (_.isEmpty(model.ccparams) || hasOnlyInvalidEntries(model.ccparams)) {
          delete model.ccparams;
        }

        if (_.isEmpty(model.coparams) || hasOnlyInvalidEntries(model.coparams)) {
          delete model.coparams;
        }

        // update current program ccparams, if applicable
        updateCCParams(model);

        $http.post('/api/model/costcoverage/effect', model).success(function (response) {
          $scope.graphs.plotdata[graphIndex] = setUpPlotdataGraph(response.plotdata);
          $scope.graphs.plotdata_co[graphIndex] = setUpPlotdataGraph(response.plotdata_co);
          effectNames[graphIndex] = response.effect;
        });
      }
    },500);

    /**
     * Collects all existing charts in the $scope.chartsForDataExport variable.
     * In addition all titles are gatherd into titlesForChartsExport. This is
     * needed since the cost coverage graphs have no title on the graphs.
     */
    var updateDataForExport = function() {
      $scope.chartsForDataExport = [];
      $scope.titlesForChartsExport = [];

      if ( $scope.ccGraph) {
        $scope.chartsForDataExport.push($scope.ccGraph);
        $scope.titlesForChartsExport.push($scope.ccGraph.options.title);
      }

      var charts = _(_.zip($scope.graphs.plotdata, $scope.graphs.plotdata_co)).flatten();
      _( charts ).each(function (chart,index) {
        $scope.chartsForDataExport.push(chart);
        $scope.titlesForChartsExport.push(chart.options.title);
      });
    };

    $scope.$watch('graphs', updateDataForExport, true);
    $scope.$watch('ccGraph', updateDataForExport, true);

    /**
     * Retrieve and update graphs based on the current plot models only if the graphs are already rendered
     * by pressing the draw button.
     */
    $scope.updateCurves =  _.debounce(function() { // debounce a bit so we don't update immediately
      if($scope.CostCoverageForm.$valid && $scope.hasCostCoverResponse === true) {
       $scope.generateCurves();
      }
    }, 500);

    initialize();

  });


});
