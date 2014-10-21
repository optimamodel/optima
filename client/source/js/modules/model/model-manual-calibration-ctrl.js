define(['./module'], function (module) {
  'use strict';

  module.controller('ModelManualCalibrationController', function ($scope) {

      $scope.linescatteroptions = {
          chart: {
              type: 'scatterPlusLineChart',
              height: 250,
              margin: {
                  top: 20,
                  right: 20,
                  bottom: 60,
                  left: 50
              },
              useInteractiveGuideline: true,
              sizeRange: [100,100],
              xAxis: {
                  axisLabel: 'Year'
              },
              yAxis: {
                  axisLabel: 'Prevalence',
                  tickFormat: function (d) {
                      return d3.format(',.2f')(d);
                  },
                  axisLabelDistance: 35
              }
          }
      };

      $scope.linescatterdata = [
          {
              values: sinData(10),
              key: 'Model',
              color: '#ff7f0e'
          },
          {
              values: [
                  {"x":2006, "y":0.3},
                  {"x":2008, "y":0.7},
                  {"x":2014, "y":0.85},
              ],
              key: 'Data',
              color: '#A09CF0'
          }
      ];


      function sinData(koeff) {
          var sin = [];

          //Data is represented as an array of {x,y} pairs.
          for (var i = 2000; i < 2014; i++) {
              sin.push({x: i, y: Math.sin(i / koeff)});
          }

          //Line chart data should be sent as an array of series objects.
          return sin;
      }

      $scope.json = {
        headers: ['Parameter', 'Value'],
        rows: [
          {
            title: 'Param. 1',
            value: 0.23
          },
          {
            title: 'Param. 2',
            value: 0.24
          },
          {
            title: 'Param. 3',
            value: 0.82
          },
          {
            title: 'Param. 4',
            value: 0.83
          },
          {
            title: 'Param. 5',
            value: 0.71
          },
          {
            title: 'Param. 6',
            value: 0.45
          }
        ]
      };

    $scope.doneEditingParameter = function () {
      console.log("I'm editing callback. Do what you have to do with me :(");
    };

  });

});
