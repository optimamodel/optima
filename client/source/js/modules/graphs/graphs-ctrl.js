define([
  './module'
], function (module) {
  'use strict';
  module.controller('GraphsController', function ($scope, dataMocks, CONFIG) {

    // GRAPH 5
    // =======
    $scope.options5 = {
      height: 300,
      width: 900,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      xAxis: {
        axisLabel: 'Axis X',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: 'Axis Y',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    dataMocks.lineScatterError().$promise.then(function (data) {
      $scope.data5 = data;
    });



    // GRAPH 6
    // =======

    $scope.options6 = {
      height: 300,
      width: 900,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      xAxis: {
        axisLabel: 'Axis X',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: 'Axis Y',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    dataMocks.lineScatterArea().$promise.then(function (data) {
      $scope.data6 = data;
    });

    // GRAPH 7
    // =======

    $scope.options7 = {
      height: 300,
      width: 900,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      xAxis: {
        axisLabel: 'Axis X',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: 'Axis Y',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    $scope.data7 = [
      [[2001, 1], [2002, 3], [2004, 5], [2005, 6], [2006, 7]],
      [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
      [[2001, 1], [2002, 2], [2004, 20], [2005, 2], [2006, 1]]
    ];

  });
});
