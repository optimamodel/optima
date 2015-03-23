define([
  './module'
], function (module) {
  'use strict';
  module.controller('GraphsController', function ($scope, dataMocks, CONFIG) {

    // Lines
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
        axisLabel: 'Axis X'
      },
      yAxis: {
        axisLabel: 'Axis Y'
      }
    };

    dataMocks.lineScatterError().$promise.then(function (data) {
      $scope.data5 = data;
    });



    // Line + Area
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
      linesStyle: ['__color-black'],
      xAxis: {
        axisLabel: 'Axis X'
      },
      yAxis: {
        axisLabel: 'Axis Y'
      }
    };

    dataMocks.lineAreaScatter().$promise.then(function (data) {
      $scope.data6 = data;
    });

    // GRAPH 7
    // =======

    $scope.options7 = {
      height: 800,
      width: 900,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      xAxis: {
        axisLabel: 'Axis X'
      },
      yAxis: {
        axisLabel: 'Axis Y'
      }
    };

    $scope.data7 = {
      'areas': [
        [[2001, 1], [2002, 3], [2004, 5], [2005, 6], [2006, 7]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]],
        [[2001, 2], [2002, 1], [2004, 2], [2005, 2], [2006, 4]]
      ]
    };

    // GRAPH 8
    // =======

    $scope.options8 = {
      height: 300,
      width: 300,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      }
    };

    $scope.data8 = {
      slices: [
        {label: '<5', value: 2704659},
        {label: '5-13', value: 4499890},
        {label: '14-17', value: 4499890},
        {label: 'Hello my long text A', value: 5},
        {label: 'Ohhh, another long label', value: 10}
      ]
    };

    // Stacked bar chart
    // =======

    $scope.options9 = {
      legend: ['AA', 'BB', 'CC'],
      height: 300,
      width: 300,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      xAxis: {
        axisLabel: 'Axis X'
      },
      yAxis: {
        axisLabel: 'Axis Y'
      }
    };

    $scope.data9 = {
      bars: [
       [2001, [552339, 259034, 450818]],
       [2002, [85640, 42153, 74257]],
       [2003, [592339, 559034, 250818]]
      ]
    };

    // Two sided horizontal bar chart
    // =======

    $scope.options10 = {
      legend: ['AA', 'BB', 'CC'],
      height: 300,
      width: 600,
      margin: {
        top: 20,
        right: 20,
        bottom: 60,
        left: 60
      },
      leftTitle: "Left Title",
      rightTitle: "Right Title"
    };

    $scope.data10 = {
      bars: [
        ['Level 1', 12030, [552339, 259034, 450818]],
        ['Level 2', 8034, [85640, 42153, 74257]],
        ['Level 3', 2023, [592339, 559034, 250818]]
      ]
    };

    $scope.radarOptions = {};

    $scope.radarData = [{
      "axes": [{
          "value": 54,
          "axis": "SBCC"
      }, {
          "value": 45,
          "axis": "NSP"
      }, {
          "value": 60,
          "axis": "OST"
      }, {
          "value": 29,
          "axis": "MSM programs"
      }, {
          "value": 40,
          "axis": "FSW programs"
      }, {
          "value": 34,
          "axis": "ART"
      }, {
          "value": 51,
          "axis": "PMTCT"
      }]
    }, {
      "axes": [{
          "value": 12,
          "axis": "SBCC"
      }, {
          "value": 10,
          "axis": "NSP"
      }, {
          "value": 20,
          "axis": "OST"
      }, {
          "value": 25,
          "axis": "MSM programs"
      }, {
          "value": 15,
          "axis": "FSW programs"
      }, {
          "value": 24,
          "axis": "ART"
      }, {
          "value": 16,
          "axis": "PMTCT"
      }]
    }, {
      "axes": [{
          "value": 10,
          "axis": "SBCC"
      }, {
          "value": 5,
          "axis": "NSP"
      }, {
          "value": 10,
          "axis": "OST"
      }, {
          "value": 2,
          "axis": "MSM programs"
      }, {
          "value": 3,
          "axis": "FSW programs"
      }, {
          "value": 5,
          "axis": "ART"
      }, {
          "value": 10,
          "axis": "PMTCT"
      }]
    }];

  });
});
