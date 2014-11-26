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
        var chartGroup = svg.append('g').attr('class', 'chart_group');
        var axesGroup = svg.append('g').attr('class', 'axes_group');

        // initialize graphs instances
        var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize, 100);

        var scatter = scope.data.scatter;

        var lineChartInstances = [];
        var calculatedLineScales;

        _(scope.data.lines).each(function (line, index) {
          var lineChart = new d3Charts.LineChart(chartGroup, index, chartSize, 100);
          lineChartInstances.push(lineChart);

          if (index === 0) {
            calculatedLineScales = lineChart.scales(line);
          } else {
            lineChart.scales(line);
          }
        });

        scatterChartInstance.scales(scope.data.lines[0]);

        d3Charts.drawAxes(
          calculatedLineScales,
          scope.options,
          axesGroup,
          chartSize
        );

        _(lineChartInstances).each(function (lineChart, index) {
            lineChart.draw(scope.data.lines[index]);
        });

        scatterChartInstance.draw(scatter);
      }
    };
  });
});
