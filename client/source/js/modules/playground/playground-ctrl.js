define(['angular', './module'], function (angular, module) {
  'use strict';

  return module.controller('PlaygroundController', function ($scope) {

    $scope.data = [
      {
        "key": "TRU",
        "values": [
          {"x": 2000, "y": 47, size: 47, y0: 47, y1: 47, "series": 0},
          {"x": 2012, "y": 27, size: 27, y0: 27, y1: 27, "series": 0},
          {"x": 2017, "y": 19, size: 19, y0: 19, y1: 19, "series": 0},
          {"x": 2025, "y": 13, size: 13, y0: 13, y1: 13, "series": 0},
          {"x": 2035, "y": 10, size: 10, y0: 10, y1: 10, "series": 0}
        ]
      },
      {
        "key": "MIN",
        "values": [
          { "x": 2000, "y": 55, size: 55, y0: 55, y1: 55, "series": 1 },
          { "x": 2012, "y": 30, size: 30, y0: 30, y1: 30, "series": 1 },
          { "x": 2017, "y": 21, size: 21, y0: 21, y1: 21, "series": 1 },
          { "x": 2025, "y": 15, size: 15, y0: 15, y1: 15, "series": 1 },
          { "x": 2035, "y": 11, size: 11, y0: 11, y1: 11, "series": 1 }
        ]
      },
      {
        "key": "UNI",
        "values": [
          { "x": 2000, "y": 43, size: 43, y0: 43, y1: 43, "series": 2 },
          { "x": 2012, "y": 26, size: 26, y0: 26, y1: 26, "series": 2 },
          { "x": 2017, "y": 18, size: 18, y0: 18, y1: 18, "series": 2 },
          { "x": 2025, "y": 13, size: 13, y0: 13, y1: 13, "series": 2 },
          { "x": 2035, "y": 10, size: 10, y0: 10, y1: 10, "series": 2 }
        ]
      },
      {
        "key": "MSM",
        "values": [
          { "x": 2000, "y": 93, size: 93, y0: 93, y1: 93, "series": 3 },
          { "x": 2012, "y": 96, size: 96, y0: 96, y1: 96, "series": 3 },
          { "x": 2017, "y": 80, size: 80, y0: 80, y1: 80, "series": 3 },
          { "x": 2025, "y": 74, size: 74, y0: 74, y1: 74, "series": 3 },
          { "x": 2035, "y": 75, size: 75, y0: 75, y1: 75, "series": 3 }
        ]
      },
      {
        "key": "MIG",
        "values": [
          { "x": 2000, "y": 799, size: 799, y0: 799, y1: 799, "series": 4 },
          { "x": 2012, "y": 464, size: 464, y0: 464, y1: 464, "series": 4 },
          { "x": 2017, "y": 324, size: 324, y0: 324, y1: 324, "series": 4 },
          { "x": 2025, "y": 233, size: 233, y0: 233, y1: 233, "series": 4 },
          { "x": 2035, "y": 176, size: 176, y0: 176, y1: 176, "series": 4 },
        ]
      }
    ];

    $scope.options = {
      chart: {
        type: 'multiBarChart',
        height: 450,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 45
        },
        clipEdge: true,
        transitionDuration: 500,
        stacked: true,
        xAxis: {
          axisLabel: 'Year',
          showMaxMin: false,
          tickFormat: function (d) {
            return d;
          }
        },
        yAxis: {
          axisLabel: 'Number of Infections',
          axisLabelDistance: 40,
          tickFormat: function (d) {
            return d;
          }
        }
      }
    };

  });

});
