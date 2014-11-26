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

    var linescatteroptions = {
      height: 400,
      width: 800,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 100
      },
      xAxis: {
        axisLabel: 'Year',
        tickFormat: function (d) {
          return d3.format('s')(d);
        }
      },
      yAxis: {
        axisLabel: 'Prevalence (%)',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    /* Methods
     ========= */

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

          $scope.graph = {
            options: linescatteroptions,
            data: {
              lines: [],
              scatter: []
            }
          };

          var numOfLines = response.plotdata[0].ylinedata.length;

          _(response.plotdata[0].xlinedata).each(function (x, index) {
            var y = response.plotdata[0].ylinedata;
            for (var i = 0; i < numOfLines; i++) {
              if (!$scope.graph.data.lines[i]) {
                $scope.graph.data.lines[i] = [];
              }

              $scope.graph.data.lines[i].push([x, y[i][index]]);
            }
          });

          _(response.plotdata[0].xscatterdata).each(function (x, index) {
            var y = response.plotdata[0].yscatterdata;

            if (y[index]) {
              $scope.graph.data.scatter.push([x, y[index]]);
            }
          });
        } else {
          alert(response.exception);
        }
      });
    };

  });
});
