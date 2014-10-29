define(['./module'], function (module) {
  'use strict';

  module.controller('ForecastsResultsController', function ($scope) {

      $scope.pieoptions = {
          chart: {
              type: 'pieChart',
              height: 350,
              x: function(d){return d.key;},
              y: function(d){return d.y;},
              showLabels: false,
              transitionDuration: 500,
              labelThreshold: 0.01,
              legend: {
                  margin: {
                      top: 5,
                      right: 35,
                      bottom: 5,
                      left: 0
                  }
              }
          }
      };

      $scope.piedata = [
          {
              key: "Behaviour change and communication",
              y: 4
          },
          {
              key: "Female sex workers",
              y: 6
          },
          {
              key: "Men who have sex with men",
              y: 1
          },
          {
              key: "Injecting drug users",
              y: 20
          },
          {
              key: "Sexually transmitted infections",
              y: 2
          },
          {
              key: "HIV counselling and testing",
              y: 6
          },
          {
              key: "Antiretroviral therapy",
              y: 54
          },
          {
              key: "Prevention of mother-to-child transmission",
              y: 6
          }
      ];


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
                  axisLabel: 'Iteration'
              },
              yAxis: {
                  axisLabel: 'Infections',
                  tickFormat: function (d) {
                      return d3.format(',.2f')(d);
                  },
                  axisLabelDistance: 35
              }
          }
      };

      $scope.linescatterdata = [
          {
              values: sinData(150),
              key: 'Infections',
              color: '#ff7f0e'
          }
      ];


      function sinData(koeff) {
          var sin = [];

          //Data is represented as an array of {x,y} pairs.
          for (var i = 1; i < 100; i++) {
              sin.push({x: i, y: Math.sin((100-i) / koeff)});
          }

          //Line chart data should be sent as an array of series objects.
          return sin;
      }




  });

});
