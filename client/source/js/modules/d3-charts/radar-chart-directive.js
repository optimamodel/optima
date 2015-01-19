define(['./module', 'angular', 'radar-chart-d3'], function (module, angular) {
  'use strict';

  module.directive('radarChart', function (d3Charts) {
    var svg;

    var prepareOptions = function (providedOptions) {
      var options = angular.copy(providedOptions);
      options.height = 320;
      options.width = 320;
      options.margin = {
        top: 10,
        right: 10,
        bottom: 0,
        left: 10
      };
      return d3Charts.adaptOptions(options);
    };

    var drawGraph = function (data, providedOptions, rootElement) {
      var options = prepareOptions(providedOptions);

      // to prevent creating multiple graphs we want to remove the existing svg
      // element before drawing a new one.
      if (svg) {
        rootElement.find("svg").remove();
      }

      var dimensions = {
        width: options.width + options.margin.left + options.margin.right,
        height: options.height + options.margin.top + options.margin.bottom
      };

      svg = d3Charts.createSvg(rootElement[0], dimensions, options.margin);
      var chart = RadarChart.chart();
      chart.config({
        w: options.width,
        h: options.height,
        radius: 3,
        color: d3.scale.ordinal().range(['#0024ff', '#2ca02c'])
      });
      svg.append('g').classed('focus', 1).datum(data).call(chart);

      var headerGroup = svg.append('g').attr('class', 'header_group');
      d3Charts.drawTitleAndLegend(svg, options, headerGroup);
    };

    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {

        scope.$watch('data', function() {
          drawGraph(scope.data, scope.options, element);
        });

        drawGraph(scope.data, scope.options, element);
      }
    };
  });
});
