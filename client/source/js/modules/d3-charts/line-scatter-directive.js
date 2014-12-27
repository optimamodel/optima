define(['./module', './scale-helpers'], function (module, scaleHelpers) {
  'use strict';

  module.directive('lineScatterChart', function (d3Charts) {
    var svg;

    var drawGraph = function (data, options, rootElement) {
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

      // Define svg groups
      var chartGroup = svg.append('g').attr('class', 'chart_group');
      var axesGroup = svg.append('g').attr('class', 'axes_group');

      var chartSize = {
        width: options.width - options.margin.left - options.margin.right,
        height: options.height - options.margin.top - options.margin.bottom
      };

      var scatterDataExists = (data.scatter && data.scatter.length > 0);

      var lineChartInstances = [];
      var graphsScales = [];
      var yMax = 0;
      var xMax = 0;
      var yMin = Number.POSITIVE_INFINITY;
      var xMin = Number.POSITIVE_INFINITY;
      var scatterChartInstance;

      // initialize lineChart for each line and update the scales
      _(data.lines).each(function (line, index) {
        var lineColor = options.linesStyle && options.linesStyle[index];
        var lineChart = new d3Charts.LineChart(chartGroup, index, chartSize, lineColor);
        lineChartInstances.push(lineChart);
        var scales = lineChart.scales(line);
        graphsScales.push(scales);
        yMax = Math.max(yMax, scales.y.domain()[1]);
        xMax = Math.max(xMax, scales.x.domain()[1]);
        yMin = Math.min(yMin, scales.y.domain()[0]);
        xMin = Math.min(xMin, scales.x.domain()[0]);
      });

      // initialize scatterChart
      if (scatterDataExists) {
        scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize);
        var scatterScale = scatterChartInstance.scales(data.scatter);
        graphsScales.push(scatterScale);
        yMax = Math.max(yMax, scatterScale.y.domain()[1]);
        xMax = Math.max(xMax, scatterScale.x.domain()[1]);
        yMin = Math.min(yMin, scatterScale.y.domain()[0]);
        xMin = Math.min(xMin, scatterScale.x.domain()[0]);
      }

      // normalizing all graphs scales to include maximum possible x and y
      _(graphsScales).each(function (scale) {
        scale.y.domain([0, yMax]);
        scale.x.domain([Math.floor(xMin), Math.ceil(xMax)]);
      });

      options.yAxis.tickFormat = function (value) {
        var format = scaleHelpers.evaluateTickFormat(yMin, yMax);
        return scaleHelpers.customTickFormat(value, format);
      };

      d3Charts.drawAxes(
        graphsScales[0],
        options,
        axesGroup,
        chartSize
      );

      // draw available charts
      _(lineChartInstances).each(function (lineChart, index) {
        lineChart.draw(data.lines[index]);
      });
      if (scatterDataExists) {
        scatterChartInstance.draw(data.scatter);
      }
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

        scope.$watch('options', function() {
          drawGraph(scope.data, scope.options, element);
        });

        drawGraph(scope.data, scope.options, element);
      }
    };
  });
});
