define(['./module', 'radar-chart-d3'], function (module, lala) {
  'use strict';

  module.directive('radarChart', function (d3Charts) {
    var svg;

    var drawGraph = function (data, rootElement) {
      // to prevent creating multiple graphs we want to remove the existing svg
      // element before drawing a new one.
      if (svg) {
        rootElement.find("svg").remove();
      }

      var dimensions = {
        height: 550,
        width: 500
      };

      var margin = {
        top: 30,
        right: 0,
        bottom: 10,
        left: 0
      };

      var chartSize = {
        width: dimensions.width - margin.left - margin.right,
        height: dimensions.height - margin.top - margin.bottom
      };

      svg = d3Charts.createSvg(rootElement[0], dimensions, margin);
      var chart = RadarChart.chart();
      chart.config({
        w: chartSize.width,
        h: chartSize.height,
        radius: 2,
        color: d3.scale.ordinal().range(['#0024ff', '#2ca02c'])
      });
      svg.append('g').classed('focus', 1).datum(data).call(chart);
    };

    return {
      scope: {
        data: '='
      },
      link: function (scope, element) {

        scope.$watch('data', function() {
          drawGraph(scope.data, element);
        });

        drawGraph(scope.data, element);
      }
    };
  });
});
