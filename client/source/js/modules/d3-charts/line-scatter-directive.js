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
        var graphsScales = [];
        var yMax = 0;
        var xMax = 0;

        _(scope.data.lines).each(function (line, index) {
          var lineChart = new d3Charts.LineChart(chartGroup, index, chartSize, 100);
          lineChartInstances.push(lineChart);
          var scales = lineChart.scales(line);
          graphsScales.push(scales);
          yMax = Math.max(yMax, scales.y.domain()[1]);
          xMax = Math.max(xMax, scales.x.domain()[1]);
        });

        var scatterScale = scatterChartInstance.scales(scope.data.scatter);
        graphsScales.push(scatterScale);
        yMax = Math.max(yMax, scatterScale.y.domain()[1]);
        xMax = Math.max(xMax, scatterScale.x.domain()[1]);

        // normalizing all graphs scales to include maximum possible x and y
        _(graphsScales).each(function (scale) {
          scale.y.domain([0, yMax]);
          scale.x.domain([0, xMax]);
        });

        d3Charts.drawAxes(
          graphsScales[0],
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
