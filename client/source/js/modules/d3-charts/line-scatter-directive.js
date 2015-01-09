define(['./module', './scale-helpers', 'angular'], function (module, scaleHelpers, angular) {
  'use strict';

  module.directive('lineScatterChart', function (d3Charts) {
    var svg;

    var drawGraph = function (data, options, rootElement) {
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

      // Define svg groups
      var chartGroup = svg.append('g').attr('class', 'chart_group');
      var axesGroup = svg.append('g').attr('class', 'axes_group');
      var headerGroup = svg.append('g').attr('class', 'header_group');

      var chartSize = {
        width: options.width - options.margin.left - options.margin.right,
        height: options.height - options.margin.top - options.margin.bottom
      };

      var scatterDataExists = (data.scatter && data.scatter.length > 0);
      var linesDataExists = (data.lines && data.lines.length > 0);

      var hasValidMin = function(domain) {
        return (domain[0]!==null && !isNaN(domain[0]));
      };

      var lineChartInstances = [];
      var graphsScales = [];
      var yMax = 0;
      var xMax = 0;
      var yMin = Number.POSITIVE_INFINITY;
      var xMin = Number.POSITIVE_INFINITY;
      var scatterChartInstance;

      // initialize lineChart for each line and update the scales
      if (linesDataExists) {
        _(data.lines).each(function (line, index) {
          var lineColor = options.linesStyle && options.linesStyle[index];
          var lineChart = new d3Charts.LineChart(chartGroup, index, chartSize, lineColor);
          lineChartInstances.push(lineChart);
          var scales = lineChart.scales(line);
          graphsScales.push(scales);
          var x_domain = scales.x.domain();
          var y_domain = scales.y.domain();
          yMax = Math.max(yMax, y_domain[1]);
          xMax = Math.max(xMax, x_domain[1]);
          if(hasValidMin(y_domain)) {yMin = Math.min(yMin, y_domain[0])};
          if(hasValidMin(x_domain)) {xMin = Math.min(xMin, x_domain[0])};
        });
      }

      // initialize scatterChart
      if (scatterDataExists || data.limits) {
        scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize);
        var scaleSource = data.limits? data.scatter.concat(data.limits): data.scatter;
        var scatterScale = scatterChartInstance.scales(scaleSource);
        graphsScales.push(scatterScale);
        var x_domain = scatterScale.x.domain();
        var y_domain = scatterScale.y.domain();

        yMax = Math.max(yMax, y_domain[1]);
        xMax = Math.max(xMax, x_domain[1]);
        if(hasValidMin(y_domain)) {yMin = Math.min(yMin, y_domain[0])};
        if(hasValidMin(x_domain)) {xMin = Math.min(xMin, x_domain[0])};
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

      d3Charts.drawTitleAndLegend(svg, options, headerGroup);

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
          drawGraph(scope.data, angular.copy(scope.options), element);
        });

        scope.$watch('options', function() {
          drawGraph(scope.data, angular.copy(scope.options), element);
        });

        drawGraph(scope.data, angular.copy(scope.options), element);
      }
    };
  });
});
