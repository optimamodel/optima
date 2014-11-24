define(['./module'], function (module) {
  'use strict';

  module.directive('lineScatterChart', function (d3Charts) {
    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {
        var dimensions = {
          height: scope.options.height,
          width: scope.options.width
        };

        var chartSize = {
          width: scope.options.width - scope.options.margin.left - scope.options.margin.right,
          height: scope.options.height - scope.options.margin.top - scope.options.margin.bottom
        };

        var svg = d3Charts.createSvg(element[0], dimensions, scope.options.margin);

        // Define svg groups
        var chartGroup = svg.append("g").attr("class", "chart_group");
        var axesGroup = svg.append("g").attr("class", "axes_group");

        var lineChartInstance = new d3Charts.LineChart(chartGroup, '', chartSize, 100);
        var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize, 100);

        var d = scope.data;
        var lineData = d.line;

        var calculatedLineScales = lineChartInstance.scales(lineData);
        scatterChartInstance.scales(lineData);

        d3Charts.drawAxes(
          calculatedLineScales,
          scope.options,
          axesGroup,
          chartSize
        );
        lineChartInstance.draw(lineData);
        scatterChartInstance.draw(d['scatter-error']);
      }
    };
  });
});
