define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelViewCalibrationController', function ($scope, $http, meta) {

    var plotTypes;


    var initialize =function () {
      $scope.meta = meta;

      $scope.programs = _(meta.progs.long).map(function (name, index) {
        return {
          name: name,
          acronym: meta.progs.code[index]
        };
      });

      $scope.activeProgram = $scope.programs[0];

      $scope.coParams = [];

      $scope.apiData = null;

      // model parameters
      $scope.saturationCoverageLevel = 0.9;
      $scope.fundingNeededPercent = 0.2;
      $scope.fundingNeededMinValue = 800000;
      $scope.fundingNeededMaxValue = 7000000;
      $scope.behaviorWithoutMin = 0.3;
      $scope.behaviorWithoutMax = 0.5;
      $scope.behaviorWithMin = 0.7;
      $scope.behaviorWithMax = 0.9;

      plotTypes = ['plotdata', 'plotdata_cc', 'plotdata_co'];
    };

    var getLineScatterOptions = function (options, xLabel, yLabel) {
      var defaults = {
        height: 300,
        width: 450,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 100
        },
        xAxis: {
          axisLabel: xLabel || 'X',
          tickFormat: function (d) {
            return d3.format('s')(d);
          }
        },
        yAxis: {
          axisLabel: yLabel || 'Y',
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          }
        }
      };

      return _(angular.copy(defaults)).extend(options);
    };

    $scope.graphs = {
      plotdata: [],
      plotdata_cc: [],
      plotdata_co: []
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
        options: getLineScatterOptions({
          width: 300,
          height: 200,
          margin: {
            top: 20,
            right: 5,
            bottom: 40,
            left: 60
          },
          linesStyle: ['__blue', '__black __dashed', '__black __dashed']
        }, graphData.xlabel, graphData.ylabel),
        data: {
          lines: [],
          scatter: []
        }
      };

      // quit if data is empty - empty graph placeholder will be displayed
      if (!graphData.ylinedata) {
        return graph;
      }

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

      _(graphData.xscatterdata).each(function (x, index) {
        var y = graphData.yscatterdata;

        if (y[index]) {
          graph.data.scatter.push([x, y[index]]);
        }
      });

      return graph;
    };

    /**
     * Receives graphs data with plot type to calculate,
     * calculates all graphs of given type and writes them to $scope.graphs[type]
     * @param data - usually api request with graphs data
     * @param type - string
     */
    var prepareGraphsOfType = function (data, type) {
      var graph;

      if (type === 'plotdata_cc') {
        graph = {
          options: getLineScatterOptions({}, data.xlabel, data.ylabel),
          data: {
            // there is a single line for that type
            lines: [[]],
            scatter: []
          }
        };

        _(data.xlinedata).each(function (x, index) {
          var y = data.ylinedata;
          graph.data.lines[0].push([x, y[index]]);
        });

        _(data.xscatterdata).each(function (x, index) {
          var y = data.yscatterdata;

          if (y[index]) {
            graph.data.scatter.push([x, y[index]]);
          }
        });

        $scope.graphs[type] = graph;

      } else if (type === 'plotdata' || type === 'plotdata_co') {
        _(data).each(function (graphData) {
          $scope.graphs[type].push(setUpPlotdataGraph(graphData));
        });
      }
    };

    var setUpCOParamsFromEffects = function (effectnames) {
      $scope.coParams = _(effectnames).map(function (effect) {
        return [
          effect[2][0][0],
          effect[2][0][1],
          effect[2][1][0],
          effect[2][1][1]
        ];
      });
    };

    /*
     * Returns the current parameterised plot model.
     */
    var getPlotModel = function() {
      return {
        progname: $scope.activeProgram.acronym,
        ccparams: [
          $scope.saturationCoverageLevel,
          $scope.fundingNeededPercent,
          $scope.fundingNeededMinValue,
          $scope.fundingNeededMaxValue
        ],
        coparams: [
          $scope.behaviorWithoutMin,
          $scope.behaviorWithoutMax,
          $scope.behaviorWithMin,
          $scope.behaviorWithMax
        ]
      };
    };

    /*
    * Retrieve and update graphs based on the provided plot models.
    */
    var retrieveAndUpdateGraphs = function (model) {
      $http.post('/api/model/costcoverage', model).success(function (response) {
        if (response.status === 'OK') {
          $scope.apiData = response;

          setUpCOParamsFromEffects(response.effectnames);

          _(plotTypes).each(function (prop) {
            prepareGraphsOfType(response[prop], prop);
          });
        }
      });
    };

    /*
     * Retrieve and update graphs based on the current plot models.
     */
    $scope.generateCurves = function () {
      var model = getPlotModel();
      retrieveAndUpdateGraphs(model);
    };

    /*
    * Retrieve and update graphs based on the current plot models.
    *
    * The plot model gets saved in the backend.
    */
    $scope.saveModel = function () {
      var model = getPlotModel(model);
      model.doSave = true;
      retrieveAndUpdateGraphs(model);
    };

    /*
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
     *     "effectname":<effectname for the given row>,
     *     "ccparams":<ccparams>,
     *     "coparams":<coprams from the corresponding coparams block>
     *   }
     */
    $scope.updateCurve = function (graphIndex) {
      $http.post('/api/model/costcoverage/effect', {
        progname: $scope.activeProgram.acronym,
        ccparams: _([
          $scope.saturationCoverageLevel,
          $scope.fundingNeededPercent,
          $scope.fundingNeededMinValue,
          $scope.fundingNeededMaxValue
        ]).map(parseFloat),
        coparams: _($scope.coParams[graphIndex]).map(parseFloat),
        effectname: $scope.apiData.effectnames[graphIndex]
      }).success(function (response) {
        $scope.graphs.plotdata[graphIndex] = setUpPlotdataGraph(response.plotdata);
        $scope.graphs.plotdata_co[graphIndex] = setUpPlotdataGraph(response.plotdata_co);
      });
    };

    initialize();

  });
});
