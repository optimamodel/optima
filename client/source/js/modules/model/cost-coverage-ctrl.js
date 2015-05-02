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

    var effects, programs;

    var initialize = function () {
      programs = programsResource.data;

      $scope.state = {
        chartsForDataExport: [],
        titlesForChartsExport: [],
        selectionPrograms: info.programs,
        coParams: [],
        hasCostCoverResponse: false,
        selectedProgram: undefined
      };

      resetCharts();

      $scope.$watch('state.costCoverageChart', updateDataForExport, true);
      $scope.$watch('state.costOutcomeCharts', updateDataForExport, true);
      $scope.$watch('state.coverageOutcomeCharts', updateDataForExport, true);
    };

    /**
     * Returns the program by name.
     */
    function findProgram (acronym) {
      return _(programs).find(function(entry) {
        return entry.name === acronym;
      });
    }

    var resetCharts = function () {
      $scope.state.costCoverageChart = undefined;
      $scope.state.costCoverageChartTitle = undefined;
      $scope.state.costOutcomeCharts = [];
      $scope.state.coverageOutcomeCharts = [];
      $scope.state.outcomeTitles = [];
    };

    /* Methods
     ========= */

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
    var isInvalidParam = function (param) {
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
      resetCharts();

      $http.post('/api/model/costcoverage', model).success(function (response) {
        effects = response.effectnames;
        $scope.state.coParams = costCoverageHelpers.setUpCoParamsFromEffects(effects);
        $scope.state.hasCostCoverResponse = true;

        $scope.state.costCoverageChartTitle = response.fig_cc.axes[0].texts[2].text;
        $scope.state.costCoverageChart = response.fig_cc;
        $scope.state.costCoverageChart.axes[0].texts.splice(2, 1);

        $scope.state.outcomeTitles = _(response.fig_co).map(function(chart) {
          return chart.axes[0].texts[2].text;
        });
        $scope.state.coverageOutcomeCharts = response.fig_co;
        _($scope.state.coverageOutcomeCharts).each(function(chart) {
          chart.axes[0].texts.splice(2, 1);
        });
        $scope.state.costOutcomeCharts = response.fig_cco;
        _($scope.state.costOutcomeCharts).each(function(chart) {
          chart.axes[0].texts.splice(2, 1);
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
      $scope.state.saturationCoverageLevel = program.ccparams.saturation * 100 || undefined;
      $scope.state.knownMinCoverageLevel = program.ccparams.coveragelower * 100 || undefined;
      $scope.state.knownMaxCoverageLevel = program.ccparams.coverageupper * 100 || undefined;
      $scope.state.knownFundingValue = program.ccparams.funding;
      $scope.state.scaleUpParameter = program.ccparams.scaleup;
      $scope.state.nonHivDalys = program.ccparams.nonhivdalys;
      $scope.state.displayYear = program.ccparams.cpibaseyear;
      $scope.state.calculatePerPerson = program.ccparams.perperson;
      $scope.state.info = info;

      var model = getPlotModel();
      retrieveAndUpdateGraphs(model);
    };

    $scope.uploadDefault = function () {
      var message = 'Upload default cost-coverage-outcome curves will be available in a future version of Optima. We are working hard in make it happen for you!';
      modalService.inform(_.noop, 'Okay', message, 'Thanks for your interest!');
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets saved in the backend.
     */
    $scope.saveModel = function () {
      if($scope.state.CostCoverageForm.$invalid || $scope.state.CombinedAdjustmentForms.$invalid) {
        modalService.inform(_.noop, 'Ok', 'Please correct all errors on this page before proceeding.', 'Cannot save invalid model');
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
          $scope.state.costOutcomeCharts[graphIndex] = response.fig_cco;
          $scope.state.costOutcomeCharts[graphIndex].axes[0].texts.splice(2, 1);

          $scope.state.coverageOutcomeCharts[graphIndex] = response.fig_co;
          $scope.state.coverageOutcomeCharts[graphIndex].axes[0].texts.splice(2, 1);

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

      // chart data
      if ( $scope.state.costCoverageChart ) {
        $scope.state.chartsForDataExport.push($scope.state.costCoverageChart);
      }

      var charts = _(_.zip($scope.state.costOutcomeCharts, $scope.state.coverageOutcomeCharts)).flatten();
      _(charts).each(function (chart) {
        $scope.state.chartsForDataExport.push(chart);
      });

      // chart titles
      if ( $scope.state.costCoverageChartTitle ) {
        $scope.state.titlesForChartsExport.push($scope.state.costCoverageChartTitle);
      }

      _($scope.state.outcomeTitles).each(function (title) {
        // we push two titles as there are cost outcome charts & coverage outcome charts
        $scope.state.titlesForChartsExport.push(title);
        $scope.state.titlesForChartsExport.push(title);
      });
    };

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
