define(['./module', './scale-helpers', 'angular', 'underscore'], function (module, scaleHelpers, angular, _) {
  'use strict';

  module.directive('stackedAreaChart', function (d3Charts) {
    var svg;

    var colors = [
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
     * Return a line based on another line where y has the value 0
     *
     * @param {array} line - a line with [x, y] values example: [[0, 0], [0, 2]]
     */
    var generateBaseLine = function(line) {
      return _(line).map(function(dot) { return [dot[0], 0]; });
    };

    /**
    * Return a area representation based on two lines.
    *
    * @param {Array} lineA - a line with [x, y] values example: [[0, 0], [0, 0]]
    * @param {Array} lineB - a line with [x, y] values example: [[0, 1], [0, 3]]
    * @returns {Array} line - example: [[0, 0, 1], [0, 0, 3]]
    */
    var generateArea = function(lineA, lineB) {
      return _(lineA).map(function(dotA, index) {
        return [ dotA[0], dotA[1], dotA[1] + lineB[index][1] ];
      });
    };

    /**
     * Returns multiple stacked areas based on the two dimensional
     * representation of an area.
     *
     * @param {Array} data - two dimensional repr of an area like [xPos, height]
     * @returns {Array} - example: [[[0, 0, 1], [0, 0, 3]], [[0, 1, 3], [0, 3, 4]]]
     */
    var generateAreas = function(data) {
      var baseLine = generateBaseLine(data[0]);
      return _(data).map(function (line) {
        var area = generateArea(baseLine, line);
        baseLine = _(area).map(function(dot) { return [dot[0], dot[2]]; });
        return area;
      });
    };

    /**
     * Draw the stacked area chart
     */
    var drawGraph = function (data, options, rootElement) {
      options.linesStyle = colors;
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

      var graphsScales = [];
      var stackedData = generateAreas(data.areas);

      var highestLineMaxY = 0;
      var highestLine = _.chain(stackedData).last().map(function(dot) {
        highestLineMaxY = Math.max(highestLineMaxY, dot[2]);
        return [dot[0], dot[2]];
      }).value();

      // will fail now instead of hanging the browser
      if (highestLineMaxY === 0) {
        throw new Error('Graph lines should not be all zeros');
      }

      _(stackedData).each(function (area, index) {
        var areaChart = new d3Charts.AreaChart(chartGroup, chartSize, colors[index]);
        var areaScale = areaChart.scales(highestLine);
        graphsScales.push(areaScale);

        var areaData = area.map(function (dot) {
          return {
            x: dot[0],
            y0: dot[1],
            y1: dot[2]
          };
        });
        areaChart.draw(areaData);
      });

      // normalizing all graphs scales to include maximum possible x and y

      // since the areas are stacked we can use the highest point of the highest
      // area line to generate the maximum y scale
      var yMax = _(highestLine).max(function(dot){ return dot[1]; })[1];
      var xMax = _(highestLine).last()[0];
      var xMin = highestLine[0][0];

      _(graphsScales).each(function (scale) {
        scale.y.domain([0, scaleHelpers.flexCeil(yMax)]);
        scale.x.domain([Math.floor(highestLine[0][0]), scaleHelpers.flexCeil(xMax)]);
      });

      options.xAxis.tickFormat = function (value) {
        var format = scaleHelpers.evaluateTickFormat(xMin, xMax);
        return scaleHelpers.customTickFormat(value, format);
      };
      options.yAxis.tickFormat = function (value) {
        // since it's a stacked area chart yMin will always be 0
        var format = scaleHelpers.evaluateTickFormat(0, yMax);
        return scaleHelpers.customTickFormat(value, format);
      };

      d3Charts.drawAxes(
        graphsScales[0],
        options,
        axesGroup,
        chartSize
      );

      d3Charts.drawTitleAndLegend(svg, options, headerGroup);
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

        scope.$emit('chart-rendered');
      }
    };
  });
});
