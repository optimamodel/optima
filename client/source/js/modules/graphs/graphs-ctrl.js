define([
  './module'
], function (module) {
  'use strict';
  module.controller('GraphsController', function ($scope, dataMocks) {
    // GRAPH 1
    // =======

    $scope.options1 = {
      chart: {
        type: 'lineChart',
        height: 300,
        margin: {
          top: 20,
          right: 20,
          bottom: 40,
          left: 55
        },
        x: function (d) {
          return d.x;
        },
        y: function (d) {
          return d.y;
        },
        useInteractiveGuideline: true,
        dispatch: {
          stateChange: function (e) {},
          changeState: function (e) {},
          tooltipShow: function (e) {},
          tooltipHide: function (e) {}
        },
        xAxis: {
          axisLabel: 'Time (ms)'
        },
        yAxis: {
          axisLabel: 'Voltage (v)',
          tickFormat: function (d) {
            return d3.format('.02f')(d);
          },
          axisLabelDistance: 30
        },
        callback: function () {
        }
      },
      title: {
        enable: true,
        text: 'Title for Line Chart'
      },
      subtitle: {
        enable: true,
        text: 'Subtitle for simple line chart. Lorem ipsum dolor sit amet, at eam blandit sadipscing, vim adhuc sanctus disputando ex, cu usu affert alienum urbanitas.',
        css: {
          'text-align': 'center',
          'margin': '10px 13px 0px 7px'
        }
      },
      caption: {
        enable: true,
        html: '<b>Figure 1.</b> Lorem ipsum dolor sit amet, at eam blandit sadipscing, <span style="text-decoration: underline;">vim adhuc sanctus disputando ex</span>, cu usu affert alienum urbanitas. <i>Cum in purto erat, mea ne nominavi persecuti reformidans.</i> Docendi blandit abhorreant ea has, minim tantas alterum pro eu. <span style="color: darkred;">Exerci graeci ad vix, elit tacimates ea duo</span>. Id mel eruditi fuisset. Stet vidit patrioque in pro, eum ex veri verterem abhorreant, id unum oportere intellegam nec<sup>[1, <a href="https://github.com/krispo/angular-nvd3" target="_blank">2</a>, 3]</sup>.',
        css: {
          'text-align': 'justify',
          'margin': '10px 13px 0px 7px'
        }
      }
    };

    $scope.data1 = dataMocks.line();

    // GRAPH 2
    // =======

    $scope.options2 = {
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
          showMaxMin: false,
          tickFormat: function (d) {
            return d3.time.format('%x')(new Date(d))
          }
        },
        yAxis: {
          tickFormat: function (d) {
            return d3.format(',.2f')(d);
          }
        }
      }
    };

    $scope.data2 = dataMocks.stackedArea();

    // GRAPH 3
    // =======

    $scope.options3 = {
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
        staggerLabels: true,
        transitionDuration: 500,
        stacked: true,
        xAxis: {
          axisLabel: 'Time (ms)',
          showMaxMin: false,
          tickFormat: function (d) {
            return d3.format(',f')(d);
          }
        },
        yAxis: {
          axisLabel: 'Y Axis',
          axisLabelDistance: 40,
          tickFormat: function (d) {
            return d3.format(',.1f')(d);
          }
        }
      }
    };

    $scope.data3 = dataMocks.multiBar();

    // GRAPH 4
    // =======

    $scope.options4 = {
      chart: {
        type: 'pieChart',
        height: 500,
        x: function (d) {
          return d.key;
        },
        y: function (d) {
          return d.y;
        },
        showLabels: true,
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

    $scope.data4 = dataMocks.pie();

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

  });
});
