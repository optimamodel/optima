define([
  './module',
  'd3',
  'underscore'
], function (module, d3, _) {
  'use strict';

  module.controller('AnalysesController', ['$scope', function ($scope) {

    $scope.options1a = {
      chart: {
        type: 'stackedAreaChart',
        height: 450,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 40
        },
        x: function (d) {
          return d[0];
        },
        y: function (d) {
          return d[1];
        },
        useVoronoi: false,
        clipEdge: true,
        transitionDuration: 500,
        useInteractiveGuideline: true,
        xAxis: {
          axisLabel: 'Year',
          showMaxMin: false,
          tickFormat: function (d) {
            return d;
          }
        },
        yAxis: {
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          }
        }
      }
    };

    $scope.data1a = [
      {
        "key": "Low-risk males",
        "values": [
          [2000, 0.200],
          [2001, 0.199],
          [2002, 0.198],
          [2003, 0.198],
          [2004, 0.198],
          [2005, 0.198],
          [2006, 0.198],
          [2007, 0.195],
          [2008, 0.195],
          [2009, 0.195],
          [2010, 0.195],
          [2011, 0.194],
          [2012, 0.194],
          [2013, 0.194],
          [2014, 0.193],
          [2015, 0.194],
          [2016, 0.194],
          [2017, 0.194],
          [2018, 0.194],
          [2019, 0.194],
          [2020, 0.194],
        ]
      },

      {
        "key": "Low-risk females",
        "values": [
          [2000, 1.300],
          [2001, 1.28],
          [2002, 1.27],
          [2003, 1.26],
          [2004, 1.25],
          [2005, 1.245],
          [2006, 1.24],
          [2007, 1.235],
          [2008, 1.23],
          [2009, 1.228],
          [2010, 1.227],
          [2011, 1.225],
          [2012, 1.224],
          [2013, 1.219],
          [2014, 1.219],
          [2015, 1.219],
          [2016, 1.219],
          [2017, 1.219],
          [2018, 1.219],
          [2019, 1.219],
          [2020, 1.219],
        ]
      },

      {
        "key": "Direct female sex workers",
        "values": [
          [2000, 1.400],
          [2001, 1.38],
          [2002, 1.37],
          [2003, 1.36],
          [2004, 1.35],
          [2005, 1.345],
          [2006, 1.34],
          [2007, 1.335],
          [2008, 1.33],
          [2009, 1.327],
          [2010, 1.326],
          [2011, 1.325],
          [2012, 1.324],
          [2013, 1.317],
          [2014, 1.317],
          [2015, 1.317],
          [2016, 1.316],
          [2017, 1.316],
          [2018, 1.315],
          [2019, 1.315],
          [2020, 1.315]
        ]
      },

      {
        "key": "Men who have sex with men",
        "values": [
          [2000, 2.600],
          [2001, 0.199],
          [2002, 2.3],
          [2003, 2.2],
          [2004, 2.1],
          [2005, 2.0],
          [2006, 1.9],
          [2007, 1.8],
          [2008, 1.7],
          [2009, 1.6],
          [2010, 1.6],
          [2011, 1.5],
          [2012, 1.45],
          [2013, 1.44],
          [2014, 1.43],
          [2015, 1.42],
          [2016, 1.41],
          [2017, 1.39],
          [2018, 1.38],
          [2019, 1.37],
          [2020, 1.36]
        ]
      }
    ];
 
 /********************************** 1b **************************************/

    $scope.options1b = {
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

    $scope.data1b = [
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
 /********************************** 1c **************************************/

    $scope.options1c = {
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
        stacked: false,
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

    $scope.data1c = [
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
  }]);
});
