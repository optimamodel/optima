define(['./module', './scale-helpers'], function (module, scaleHelpers) {
  'use strict';

  module.directive('lineScatterAreaChart', function (d3Charts) {
    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {
        scope.options = d3Charts.adaptOptions(scope.options);

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
        var headerGroup = svg.append('g').attr('class', 'legend_group');

        // initialize chart instances
        var lineChartInstance = new d3Charts.LineChart(chartGroup, chartSize, '__color-black');
        var areaChartInstance = new d3Charts.AreaChart(chartGroup, chartSize, '__color-blue-1');
        var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, chartSize);

        // fetch & generate data for the graphs
        var lineData = scope.data.line;
        var scatterData = scope.data.scatter;
        var areaLineHighData = scope.data.area.lineHigh;
        var areaLineLowData = scope.data.area.lineLow;
        var areaData = areaLineHighData.map(function (dot, index) {
          return {
            x: dot[0],
            y0: dot[1],
            y1: areaLineLowData[index][1]
          };
        });

        var scatterDataExists = (scatterData && scatterData.length > 0);
        var graphsScales = [];

        // normalizing all graphs scales to include maximum possible x and y
        var lineScale = lineChartInstance.scales(lineData);
        graphsScales.push(lineScale);
        var areaScale = areaChartInstance.scales(areaLineHighData);
        graphsScales.push(areaScale);
        if (scatterDataExists) {
          var scatterScale = scatterChartInstance.scales(scatterData);
          graphsScales.push(scatterScale);
        }

        // determine boundaries for the combined graphs
        var yMax = 0;
        var xMax = 0;
        var yMin = Number.POSITIVE_INFINITY;
        var xMin = Number.POSITIVE_INFINITY;
        _(graphsScales).each(function (scale) {
          yMax = Math.max(yMax, scale.y.domain()[1]);
          xMax = Math.max(xMax, scale.x.domain()[1]);
          yMin = Math.min(yMin, scale.y.domain()[0]);
          xMin = Math.min(xMin, scale.x.domain()[0]);
        });

        // normalize graph scales to include min and max of the combined graphs
        _(graphsScales).each(function (scale) {
          scale.y.domain([0, yMax]);
          scale.x.domain([Math.floor(xMin), scaleHelpers.flexCeil(xMax)]);
        });

        scope.options.yAxis.tickFormat = function (value) {
          var format = scaleHelpers.evaluateTickFormat(0, yMax);
          return scaleHelpers.customTickFormat(value, format);
        };

        d3Charts.drawAxes(
          graphsScales[0],
          scope.options,
          axesGroup,
          chartSize
        );

        d3Charts.drawTitleAndLegend(svg, scope.options, headerGroup);

        // draw graphs
        areaChartInstance.draw(areaData);
        lineChartInstance.draw(lineData);
        if (scatterDataExists) {
          scatterChartInstance.draw(scatterData);
        }
      }
    };
  });
});
