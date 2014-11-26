define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelViewCalibrationController', function ($scope, $http, meta) {

    /* Initialization
     ================ */
    $scope.meta = meta;

    $scope.programs = _(meta.progs.long).map(function (name, index) {
      return {
        name: name,
        acronym: meta.progs.code[index]
      };
    });

    $scope.activeProgram = $scope.programs[0];

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

    var getLineScatterOptions = function (options, xLabel, yLabel) {
      var defaults = {
        height: 400,
        width: 800,
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

    var prepareGraph = function (data, type) {
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

      } else if (type === 'plotdata') {

        _(data).each(function (graphData) {
          var graph = {
            options: getLineScatterOptions({}, graphData.xlabel, graphData.ylabel),
            data: {
              lines: [],
              scatter: []
            }
          };

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

          $scope.graphs[type].push(graph);
        });
      }
    };

    $scope.generateCurves = function () {
      $http.post('/api/model/costcoverage', {
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
      }).success(function (response) {
        if (response.status === 'OK') {
          $scope.apiData = response;

          _(['plotdata', 'plotdata_cc', 'plotdata_co']).each(function (prop) {
            prepareGraph(response[prop], prop);
          });
        } else {
          alert(response.exception);
        }
      });
    };

  });
});
