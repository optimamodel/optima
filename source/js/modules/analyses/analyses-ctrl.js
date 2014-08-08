define([
  './module',
  'underscore'
], function (module, _) {
  'use strict';

  module.controller('AnalysesController', ['$scope', function ($scope) {

    $scope.rawdata1a = [
      {"x":2000,"val_0":0.200,"val_1":1.3,"val_2":1.4,"val_3":2.6,"val_4":4.0},
      {"x":2001,"val_0":0.199,"val_1":1.28,"val_2":1.38,"val_3":2.5,"val_4":3.8},
      {"x":2002,"val_0":0.198,"val_1":1.27,"val_2":1.37,"val_3":2.3,"val_4":3.7},
      {"x":2003,"val_0":0.198,"val_1":1.26,"val_2":1.36,"val_3":2.2,"val_4":3.65},
      {"x":2004,"val_0":0.198,"val_1":1.25,"val_2":1.35,"val_3":2.1,"val_4":3.6},
      {"x":2005,"val_0":0.198,"val_1":1.245,"val_2":1.345,"val_3":2.0,"val_4":3.56},
      {"x":2006,"val_0":0.198,"val_1":1.24,"val_2":1.34,"val_3":1.9,"val_4":3.5},
      {"x":2007,"val_0":0.195,"val_1":1.235,"val_2":1.335,"val_3":1.8,"val_4":3.4},
      {"x":2008,"val_0":0.195,"val_1":1.23,"val_2":1.33,"val_3":1.7,"val_4":3.33},
      {"x":2009,"val_0":0.195,"val_1":1.228,"val_2":1.327,"val_3":1.6,"val_4":3.31},
      {"x":2010,"val_0":0.195,"val_1":1.227,"val_2":1.326,"val_3":1.6,"val_4":3.29},
      {"x":2011,"val_0":0.194,"val_1":1.225,"val_2":1.325,"val_3":1.5,"val_4":3.285},
      {"x":2012,"val_0":0.194,"val_1":1.224,"val_2":1.324,"val_3":1.45,"val_4":3.284},
      {"x":2013,"val_0":0.194,"val_1":1.219,"val_2":1.317,"val_3":1.44,"val_4":3.283},
      {"x":2014,"val_0":0.193,"val_1":1.219,"val_2":1.317,"val_3":1.43,"val_4":3.282},
      {"x":2015,"val_0":0.194,"val_1":1.219,"val_2":1.317,"val_3":1.42,"val_4":3.281},
      {"x":2016,"val_0":0.194,"val_1":1.219,"val_2":1.316,"val_3":1.41,"val_4":3.279},
      {"x":2017,"val_0":0.194,"val_1":1.219,"val_2":1.316,"val_3":1.39,"val_4":3.145},
      {"x":2018,"val_0":0.194,"val_1":1.219,"val_2":1.315,"val_3":1.38,"val_4":3.058},
      {"x":2019,"val_0":0.194,"val_1":1.219,"val_2":1.315,"val_3":1.37,"val_4":2.956},
      {"x":2020,"val_0":0.194,"val_1":1.219,"val_2":1.315,"val_3":1.36,"val_4":2.825}
    ];

    $scope.subFixed = function(arg1, arg2) {
      return parseFloat((arg1-arg2).toFixed(3));
    };

    $scope.toStacked = function(data) {
      var result = [];
      _(data).each(function(elem) {
        elem.val_4 = $scope.subFixed(elem.val_4, elem.val_3);
        elem.val_3 = $scope.subFixed(elem.val_3, elem.val_2);
        elem.val_2 = $scope.subFixed(elem.val_2, elem.val_1);
        result.push(elem);
      });
      return result;
    };

    $scope.data1a = $scope.toStacked($scope.rawdata1a);

    $scope.options1a = {
      stacks: [{axis: "y", series: ["series_0", "series_1", "series_2", "series_3", "series_4"]}],
      series: [
        {
          y: "val_0",
          label: "Low-risk males",
          color: "#01008e",
          axis: "y",
          type: "area",
          thickness: "5px",
          id: "series_0"
        },
        {
          y: "val_1",
          label: "Low-risk females",
          color: "#008fff",
          type: "area",
          axis: "y",
          thickness: "5px",
          id: "series_1"
        },
        {
          y: "val_2",
          label: "Direct female sex workers",
          color: "#b4b4b4",
          type: "area",
          axis: "y",
          thickness: "5px",
          id: "series_2"
        },
        {
          y: "val_3",
          label: "Men who have sex with men",
          color: "#fc6c00",
          type: "area",
          axis: "y",
          thickness: "5px",
          id: "series_3"
        },
        {
          y: "val_4",
          label: "Male high-risk drug users",
          color: "#7e0001",
          type: "area",
          axis: "y",
          thickness: "5px",
          id: "series_4"
        }
      ],
      axes: {x: {type: "linear", key: "x"}, y: {type: "linear"}},
      lineMode: "cardinal",
      tension: 0.7,
      tooltip: {mode: "scrubber"},
      drawLegend: true,
      drawDots: true,
      columnsHGap: 5
    };
 
 /********************************** 1b **************************************/

  $scope.data1b = [
    {"x":2000,"val_0":47,"val_1":55,"val_2":43,"val_3":93,"val_4":799,"val_5":28,"val_6":680,
      "val_7":405,"val_8":107,"val_9":1010,"val_10":1223,"val_11":49, "val_12":595,"val_13":2337},
    {"x":2012,"val_0":27,"val_1":30,"val_2":26,"val_3":96,"val_4":464,"val_5":17,"val_6":350,
      "val_7":237,"val_8":56,"val_9":543,"val_10":499,"val_11":17, "val_12":184,"val_13":806},
    {"x":2017,"val_0":19,"val_1":21,"val_2":18,"val_3":80,"val_4":324,"val_5":12,"val_6":241,
      "val_7":164,"val_8":38,"val_9":376,"val_10":327,"val_11":11, "val_12":117,"val_13":659},
    {"x":2025,"val_0":13,"val_1":15,"val_2":13,"val_3":74,"val_4":233,"val_5":9,"val_6":173,
      "val_7":118,"val_8":27,"val_9":269,"val_10":220,"val_11":8, "val_12":75,"val_13":480},
    {"x":2035,"val_0":10,"val_1":11,"val_2":10,"val_3":75,"val_4":176,"val_5":7,"val_6":132,
      "val_7":89,"val_8":20,"val_9":202,"val_10":161,"val_11":6, "val_12":54,"val_13":338}
  ];

  $scope.options1b = {
      stacks: [{axis: "y", series: [
        "series_0", "series_1", "series_2", "series_3", "series_4", "series_5", "series_6",
        "series_7", "series_8", "series_9", "series_10", "series_11", "series_12", "series_13"
      ]}],
      series: [
        {
          y: "val_0",
          label: "TRU",
          color: "#4A7EB0",
          axis: "y",
          type: "column",
          thickness: "5px",
          id: "series_0"
        },
        {
          y: "val_1",
          label: "MIN",
          color: "#EC7D31",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_1"
        },
        {
          y: "val_2",
          label: "UNI",
          color: "#FFBF00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_2"
        },
        {
          y: "val_3",
          label: "MSM",
          color: "#fc6c00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_3"
        },
        {
          y: "val_4",
          label: "MIG",
          color: "#7e0001",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_4"
        },
        {
          y: "val_5",
          label: "PRI",
          color: "#4A7EB0",
          axis: "y",
          type: "column",
          thickness: "5px",
          id: "series_5"
        },
        {
          y: "val_6",
          label: "FSW",
          color: "#EC7D31",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_6"
        },
        {
          y: "val_7",
          label: "MELD",
          color: "#FFBF00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_7"
        },
        {
          y: "val_8",
          label: "FELD",
          color: "#fc6c00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_8"
        },
        {
          y: "val_9",
          label: "MAD",
          color: "#7e0001",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_9"
        },
        {
          y: "val_10",
          label: "FAD",
          color: "#FFBF00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_10"
        },
        {
          y: "val_11",
          label: "MYTH",
          color: "#fc6c00",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_11"
        },
        {
          y: "val_12",
          label: "PYTH",
          color: "#7e0001",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_12"
        },
        {
          y: "val_6",
          label: "CHLD",
          color: "#EC7D31",
          type: "column",
          axis: "y",
          thickness: "5px",
          id: "series_13"
        }
      ],
      axes: {x: {type: "linear", key: "x"}, y: {type: "linear"}},
      lineMode: "cardinal",
      tension: 0.7,
      tooltip: {mode: "scrubber"},
      drawLegend: true,
      drawDots: true,
      columnsHGap: 20
    };
 
  }]);
});
