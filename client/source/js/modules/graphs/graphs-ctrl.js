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

    $scope.data5 = dataMocks.lineScatterError();

    // GRAPH 6

    $scope.options6 = {
      "chart": {
        "type": "multiChart",
        "height": 450,
        "margin": {
          "top": 90,
          "right": 60,
          "bottom": 50,
          "left": 70
        },
        "color": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
        "transitionDuration": 500,
        "xAxis": {},
        "yAxis1": {},
        "yAxis2": {}
      }
    };

    $scope.data6 = [
      {"key": "Stream0", "values": [
        {"x": 0, "y": -0.1226294589464796, "index": 0, "seriesIndex": 0, "display": {"y": -0.1226294589464796, "y0": 0}, "series": 0},
        {"x": 1, "y": -0.19602712790947407, "index": 1, "seriesIndex": 0, "display": {"y": -0.19602712790947407, "y0": 0}, "series": 0},
        {"x": 2, "y": -0.10057828429493322, "index": 2, "seriesIndex": 0, "display": {"y": -0.10057828429493322, "y0": 0}, "series": 0},
        {"x": 3, "y": -0.1663626835754104, "index": 3, "seriesIndex": 0, "display": {"y": -0.1663626835754104, "y0": 0}, "series": 0},
        {"x": 4, "y": -0.3671732869992546, "index": 4, "seriesIndex": 0, "display": {"y": -0.3671732869992546, "y0": 0}, "series": 0},
        {"x": 5, "y": -3.161954945181476, "index": 5, "seriesIndex": 0, "display": {"y": -3.161954945181476, "y0": 0}, "series": 0},
        {"x": 6, "y": -0.8164131881344071, "index": 6, "seriesIndex": 0, "display": {"y": -0.8164131881344071, "y0": 0}, "series": 0},
        {"x": 7, "y": -2.1140764413826876, "index": 7, "seriesIndex": 0, "display": {"y": -2.1140764413826876, "y0": 0}, "series": 0},
        {"x": 8, "y": -0.6900162328385322, "index": 8, "seriesIndex": 0, "display": {"y": -0.6900162328385322, "y0": 0}, "series": 0},
        {"x": 9, "y": -0.16640672280758323, "index": 9, "seriesIndex": 0, "display": {"y": -0.16640672280758323, "y0": 0}, "series": 0},
        {"x": 10, "y": -0.12089644227573496, "index": 10, "seriesIndex": 0, "display": {"y": -0.12089644227573496, "y0": 0}, "series": 0}
      ], "type": "area", "yAxis": 1, "originalKey": "Stream0", "seriesIndex": 0},
      {"key": "Stream1", "values": [
        {"x": 0, "y": -0.14825540847664412, "index": 0, "seriesIndex": 1, "display": {"y": -0.14825540847664412, "y0": -0.1226294589464796}, "series": 1},
        {"x": 1, "y": -0.16539480867829576, "index": 1, "seriesIndex": 1, "display": {"y": -0.16539480867829576, "y0": -0.19602712790947407}, "series": 1},
        {"x": 2, "y": -0.3369077234096044, "index": 2, "seriesIndex": 1, "display": {"y": -0.3369077234096044, "y0": -0.10057828429493322}, "series": 1},
        {"x": 3, "y": -1.335289712359094, "index": 3, "seriesIndex": 1, "display": {"y": -1.335289712359094, "y0": -0.1663626835754104}, "series": 1},
        {"x": 4, "y": -1.1700230706172512, "index": 4, "seriesIndex": 1, "display": {"y": -1.1700230706172512, "y0": -0.3671732869992546}, "series": 1},
        {"x": 5, "y": -0.7109760993829533, "index": 5, "seriesIndex": 1, "display": {"y": -0.7109760993829533, "y0": -3.161954945181476}, "series": 1},
        {"x": 6, "y": -1.0875463401588594, "index": 6, "seriesIndex": 1, "display": {"y": -1.0875463401588594, "y0": -0.8164131881344071}, "series": 1},
        {"x": 7, "y": -6.2477134050249425, "index": 7, "seriesIndex": 1, "display": {"y": -6.2477134050249425, "y0": -2.1140764413826876}, "series": 1},
        {"x": 8, "y": -4.609332630304903, "index": 8, "seriesIndex": 1, "display": {"y": -4.609332630304903, "y0": -0.6900162328385322}, "series": 1},
        {"x": 9, "y": -0.5290202135393085, "index": 9, "seriesIndex": 1, "display": {"y": -0.5290202135393085, "y0": -0.16640672280758323}, "series": 1},
        {"x": 10, "y": -0.18222312111731523, "index": 10, "seriesIndex": 1, "display": {"y": -0.18222312111731523, "y0": -0.12089644227573496}, "series": 1}
      ], "type": "area", "yAxis": 1, "originalKey": "Stream1", "seriesIndex": 1},
      {"key": "Stream2", "values": [
        {"x": 0, "y": 4.516346426300862, "series": 0},
        {"x": 1, "y": 1.1149646800101014, "series": 0},
        {"x": 2, "y": 0.2512799707763466, "series": 0},
        {"x": 3, "y": 0.15152473251901988, "series": 0},
        {"x": 4, "y": 0.1860198663932899, "series": 0},
        {"x": 5, "y": 0.3434112691060634, "series": 0},
        {"x": 6, "y": 2.1332828119687828, "series": 0},
        {"x": 7, "y": 2.2964213540571032, "series": 0},
        {"x": 8, "y": 0.45146916741113746, "series": 0},
        {"x": 9, "y": 0.1560024169405767, "series": 0},
        {"x": 10, "y": 0.14305812720933475, "series": 0}
      ], "type": "line", "yAxis": 1, "originalKey": "Stream2"},
      {"key": "Stream3 (right axis)", "values": [
        {"x": 0, "y": 0.19060678435096637, "series": 0},
        {"x": 1, "y": 0.9426604448455809, "series": 0},
        {"x": 2, "y": 0.5793613490053421, "series": 0},
        {"x": 3, "y": 0.18730480731034513, "series": 0},
        {"x": 4, "y": 0.15214927272310985, "series": 0},
        {"x": 5, "y": 0.1752613935083468, "series": 0},
        {"x": 6, "y": 0.15742735871454264, "series": 0},
        {"x": 7, "y": 0.17461350641403625, "series": 0},
        {"x": 8, "y": 0.17270410757352875, "series": 0},
        {"x": 9, "y": 1.4291667320415278, "series": 0},
        {"x": 10, "y": 1.0074209522654864, "series": 0}
      ], "type": "line", "yAxis": 2, "originalKey": "Stream3"},
      {"key": "Stream4 (right axis)", "values": [
        {"x": 0, "y": 0.3985764334968057, "series": 0},
        {"x": 1, "y": 0.1738308143320343, "series": 0},
        {"x": 2, "y": 0.13552804848719077, "series": 0},
        {"x": 3, "y": 0.19764553520344544, "series": 0},
        {"x": 4, "y": 0.15949786182036593, "series": 0},
        {"x": 5, "y": 0.11719635750429755, "series": 0},
        {"x": 6, "y": 0.5518628719234597, "series": 0},
        {"x": 7, "y": 0.2411520722632518, "series": 0},
        {"x": 8, "y": 0.10394358574894996, "series": 0},
        {"x": 9, "y": 0.16172522397246214, "series": 0},
        {"x": 10, "y": 0.19934794791042806, "series": 0}
      ], "type": "bar", "yAxis": 2, "originalKey": "Stream4"},
      {"key": "Stream5 (right axis)", "values": [
        {"x": 0, "y": 0.14402389491821313, "series": 1},
        {"x": 1, "y": 1.0915519697803668, "series": 1},
        {"x": 2, "y": 0.15241092443683452, "series": 1},
        {"x": 3, "y": 0.17162819919271033, "series": 1},
        {"x": 4, "y": 0.16840457948856058, "series": 1},
        {"x": 5, "y": 0.15942026854027064, "series": 1},
        {"x": 6, "y": 0.26200631696859716, "series": 1},
        {"x": 7, "y": 0.12783773962373232, "series": 1},
        {"x": 8, "y": 0.10379951397883015, "series": 1},
        {"x": 9, "y": 0.10937742230120671, "series": 1},
        {"x": 10, "y": 0.4770455457570464, "series": 1}
      ], "type": "bar", "yAxis": 2, "originalKey": "Stream5"},
      {"key": "Stream6 (right axis)", "values": [
        {"x": 0, "y": 0.21897533860713564, "series": 2},
        {"x": 1, "y": 0.11153963852310758, "series": 2},
        {"x": 2, "y": 0.10793855844659114, "series": 2},
        {"x": 3, "y": 0.1474132805406848, "series": 2},
        {"x": 4, "y": 0.15132439208216356, "series": 2},
        {"x": 5, "y": 0.6620405529710952, "series": 2},
        {"x": 6, "y": 2.391731837764878, "series": 2},
        {"x": 7, "y": 2.1824422891053614, "series": 2},
        {"x": 8, "y": 2.9711017087790292, "series": 2},
        {"x": 9, "y": 3.587842910455618, "series": 2},
        {"x": 10, "y": 1.0414941973868754, "series": 2}
      ], "type": "bar", "yAxis": 2, "originalKey": "Stream6"}
    ];

  });
});
