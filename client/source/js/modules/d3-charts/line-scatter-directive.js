define(['./module', './scale-helpers', 'angular'], function (module, scaleHelpers, angular) {
  'use strict';

  module.directive('lineScatterChart', function (d3Charts) {
    var svg;

    function hasValidMin(domain) {
      return (domain[0]!==null && !isNaN(domain[0]));
    }

    // see available colors in chart/_color.scss.
    var colors = [
      '__color-blue-4',
      '__color-blue-5',
      '__color-grey-4',
      '__color-grey-5',
      '__color-purple-4',
      '__color-purple-5',
      '__color-brown-4',
      '__color-brown-5',
      '__color-green-4',
      '__color-green-5',
      '__color-deep-blue-4',
      '__color-deep-blue-5',
      '__color-yellow-4',
      '__color-yellow-5',
      '__color-salmon-4',
      '__color-salmon-5'
    ];

    function drawGraph(data, options, rootElement) {
      options.linesStyle = options.linesStyle || colors;
      options.areasStyle = options.areasStyle || colors;
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

      var scatterDataExists = (data.scatter && (data.scatter.length > 0));
      var linesDataExists = (data.lines && data.lines.length > 0);
      var areasDataExists = (data.areas && data.areas.length > 0);

      var lineChartInstances = [];
      var areaChartInstances = [];
      var areasData = [];
      var graphsScales = [];
      var yMax = 0;
      var xMax = 0;
      var yMin = Number.POSITIVE_INFINITY;
      var xMin = Number.POSITIVE_INFINITY;
      var scatterChartInstance;

      // initialize lineChart for each line and update the scales
      if (linesDataExists) {
        _(data.lines).each(function (line, index) {
          var lineColor = options.linesStyle[index];
          var lineChart = new d3Charts.LineChart(chartGroup, chartSize, lineColor);
          lineChartInstances.push(lineChart);
          var scales = lineChart.scales(line);
          graphsScales.push(scales);
          var x_domain = scales.x.domain();
          var y_domain = scales.y.domain();
          yMax = Math.max(yMax, y_domain[1]);
          xMax = Math.max(xMax, x_domain[1]);
          if(hasValidMin(y_domain)) { yMin = Math.min(yMin, y_domain[0]); }
          if(hasValidMin(x_domain)) { xMin = Math.min(xMin, x_domain[0]); }
        });
      }

      // initialize areas
      if (areasDataExists) {
        _(data.areas).each(function (area, index) {
          var color = options.areasStyle[index];

          var areaChart = new d3Charts.AreaChart(chartGroup, chartSize, color);
          areaChartInstances.push(areaChart);

          var areaData = area.lineHigh.map(function (dot, index) {
            return {
              x: dot[0],
              y0: dot[1],
              y1: area.lineLow[index][1]
            };
          });
          areasData.push(areaData);

          var scales = areaChart.scales(area.lineHigh);
          graphsScales.push(scales);
          var x_domain = scales.x.domain();
          var y_domain = scales.y.domain();
          yMax = Math.max(yMax, y_domain[1]);
          xMax = Math.max(xMax, x_domain[1]);
          if(hasValidMin(y_domain)) { yMin = Math.min(yMin, y_domain[0]); }
          if(hasValidMin(x_domain)) { xMin = Math.min(xMin, x_domain[0]); }

        });
      }

      // initialize scatterChart
      if (scatterDataExists || data.limits) {
        scatterChartInstance = new d3Charts.ScatterChart(chartGroup, chartSize);
        var scaleSource = data.limits? data.scatter.concat(data.limits): data.scatter;
        var scatterScale = scatterChartInstance.scales(scaleSource);
        graphsScales.push(scatterScale);
        var x_domain = scatterScale.x.domain();
        var y_domain = scatterScale.y.domain();
        yMax = Math.max(yMax, y_domain[1]);
        xMax = Math.max(xMax, x_domain[1]);
        if(hasValidMin(y_domain)) { yMin = Math.min(yMin, y_domain[0]); }
        if(hasValidMin(x_domain)) { xMin = Math.min(xMin, x_domain[0]); }
      }

      // to make it visually appealing in case there is a point but no line
      // the data point is centered
      if (xMin == xMax) {
        xMin = xMin - 1;
        xMax = xMax + 1;
      }

      // normalize graph scales to include min and max of the combined graphs
      _(graphsScales).each(function (scale) {
        scale.y.domain([yMin, yMax]);
        scale.x.domain([Math.floor(xMin), scaleHelpers.flexCeil(xMax)]);
      });

      options.yAxis.tickFormat = function (value) {
        var format = scaleHelpers.evaluateTickFormat(yMin, yMax);
        return scaleHelpers.customTickFormat(value, format);
      };

      options.xAxis.tickFormat = function (value) {
        var format = scaleHelpers.evaluateTickFormat(xMin, xMax);
        return scaleHelpers.customTickFormat(value, format);
      };

      console.log(graphsScales);

      d3Charts.drawAxes(
        graphsScales[0],
        options,
        axesGroup,
        chartSize
      );

      d3Charts.drawTitleAndLegend(svg, options, headerGroup);

      _(areaChartInstances).each(function (areaChart, index) {
        areaChart.draw(areasData[index]);
      });

      // draw available charts
      _(lineChartInstances).each(function (lineChart, index) {
        lineChart.draw(data.lines[index]);
      });
      if (scatterDataExists) {
        scatterChartInstance.draw(data.scatter);
      }
    }

    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {

        scope.$watchCollection('[data,options]', function() { // before this change, all the graphs were redrawn three times
          drawGraph(scope.data, angular.copy(scope.options), element);
        });
      }
    };
  });
});
