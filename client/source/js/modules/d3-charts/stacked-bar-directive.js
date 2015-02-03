define(['./module', './scale-helpers', 'angular', './stacked-bar-chart'], function (module, scaleHelpers, angular, StackedBarChart) {
  'use strict';

  module.directive('stackedBarChart', function (d3Charts) {
    var svg;

    var defaultColors = [
      '__color-blue-1',
      '__color-blue-2',
      '__color-blue-3',
      '__color-grey-1',
      '__color-grey-2',
      '__color-grey-3',
      '__color-purple-1',
      '__color-purple-2',
      '__color-purple-3',
      '__color-brown-1',
      '__color-brown-2',
      '__color-brown-3',
      '__color-green-1',
      '__color-green-2',
      '__color-green-3',
      '__color-deep-blue-1',
      '__color-deep-blue-2',
      '__color-deep-blue-3',
      '__color-yellow-1',
      '__color-yellow-2',
      '__color-yellow-3',
      '__color-salmon-1',
      '__color-salmon-2',
      '__color-salmon-3'
    ];

    /**
     * Draw the stacked bar chart
     */
    var drawGraph = function (data, options, rootElement) {
      options.linesStyle = options.linesStyle || defaultColors;
      options = d3Charts.adaptOptions(options);

      // to prevent creating multiple graphs we want to remove the existing svg
      // element before drawing a new one.
      if (svg) {
        rootElement.find("svg").remove();
      }

      var dimensions = {
        height: options.height,
        width: options.width
      };

      svg = d3Charts.createSvg(rootElement[0], dimensions, options.margin);

      var chartSize = {
        width: options.width - options.margin.left - options.margin.right,
        height: options.height - options.margin.top - options.margin.bottom
      };

      // Define svg groups
      var chartGroup = svg.append('g').attr('class', 'chart_group');
      var axesGroup = svg.append('g').attr('class', 'axes_group');
      var headerGroup = svg.append('g').attr('class', 'header_group');

      var chart = new StackedBarChart(chartGroup, chartSize, data.bars, options.linesStyle);
      chart.draw();
      d3Charts.drawTitleAndLegend(svg, options, headerGroup);

      // since the xAxis is ordinal we don't need a tickformat for it
      options.yAxis.tickFormat = function (value) {
        // since it's a stacked bar chart yMin will always be 0
        var format = scaleHelpers.evaluateTickFormat(0, chart.yMax());
        return scaleHelpers.customTickFormat(value, format);
      };

      d3Charts.drawAxes(
        chart.axisScales(),
        options,
        axesGroup,
        chartSize
      );

    };

    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {
        // before this change, all the graphs were redrawn three times
        scope.$watchCollection('[data,options]', function() {
          drawGraph(scope.data, angular.copy(scope.options), element);
        });
      }
    };
  });
});
