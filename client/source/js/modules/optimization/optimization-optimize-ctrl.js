define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('OptimizationOptimizeController', function ($scope, $http) {

    $scope.pie1 = { title: '', data: [] };
    $scope.pie2 = { title: '', data: [] };

    $scope.linescatterdata = [{ "values": [], "key": "Infections", "color": "#ff7f0e" }];


    // @todo now it's just mocked labels
    var pieLabels = [
      "Behaviour change and communication",
      "Female sex workers",
      "Men who have sex with men",
      "Injecting drug users",
      "Sexually transmitted infections",
      "HIV counselling and testing",
      "Antiretroviral therapy",
      "Prevention of mother-to-child transmission"
    ];

    var setupPie = function (container, data) {
      container.title = data.title;
      container.data = _(data.piedata).map(function (value, i) {
        return {
          key: pieLabels[i],
          y: value
        };
      });
    };

    var setupLine = function (container, options, data) {
      options.xAxis.axisLabel = data.xlabel;
      options.yAxis.axisLabel = data.ylabel;
      container.values = _(data.xmodeldata).map(function (value, i) {
        return {
          series: 0,
          x: value,
          y: data.ymodeldata[i]
        };
      });
    };

    $scope.startRun = false;
    $scope.startAnalysis = function () {
      $http.get('/api/analysis/optimisation/start')
        .success(function (response) {
          if (response.dataplot && response.lineplot) {
            setupPie($scope.pie1, response.dataplot[0]);
            setupPie($scope.pie2, response.dataplot[1]);
            setupLine($scope.linescatterdata, $scope.linescatteroptions, response.lineplot[0]);
            $scope.startRun = true;
          } else {
            alert(response.reason);
          }
        });
    };

    $scope.pieoptions = {
      chart: {
        type: 'pieChart',
        height: 350,
        x: function (d) {
          return d.key;
        },
        y: function (d) {
          return d.y;
        },
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
        sizeRange: [100, 100],
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
  });

});
