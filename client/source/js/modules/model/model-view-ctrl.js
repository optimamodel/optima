define(['./module'], function (module) {
  'use strict';

  module.controller('ModelViewController', function ($scope) {

    $scope.options = {
      chart: {
        type: 'lineChart',
        height: 150,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 50
        },
        xAxis: {
          axisLabel: 'X Axis'
        },
        yAxis: {
          axisLabel: 'Y Axis',
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          },
          axisLabelDistance: 35
        }
      }
    };

    $scope.data = [
      {
        values: sinData(200),
        key: 'Sine Wave 1',
        color: '#ff7f0e'
      },
      {
        values: sinData(150),
        key: 'Sine Wave 2',
        color: '#2ca02c'
      },
      {
        values: sinData(100),
        key: 'Sine Wave 3',
        color: '#A09CF0'
      }
    ];

    function sinData(koeff) {
      var sin = [];

      //Data is represented as an array of {x,y} pairs.
      for (var i = 0; i < 500; i++) {
        sin.push({x: i, y: Math.sin(i / koeff)});
      }

      //Line chart data should be sent as an array of series objects.
      return sin;
    }

  });

});
