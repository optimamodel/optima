define(['./module', './scale-helpers', 'angular'], function (module, scaleHelpers, angular) {
  'use strict';

  module.directive('stackedAreaChart', function (d3Charts) {
    var svg;

    var colors = [
      'color-1',
      'color-2',
      'color-3',

      'color-10',
      'color-11',
      'color-12',

      'color-7',
      'color-8',
      'color-9',

      'color-13',
      'color-14',
      'color-15',

      'color-4',
      'color-5',
      'color-6',

      'color-16',
      'color-17',
      'color-18',

      'color-19',
      'color-20',
      'color-21',

      'color-22',
      'color-23',
      'color-24',
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
      var highestLine = _.chain(stackedData).last().map(function(dot) { return [dot[0], dot[2]]; }).value();

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

      _(graphsScales).each(function (scale) {
        scale.y.domain([0, scaleHelpers.flexCeil(yMax)]);
        scale.x.domain([Math.floor(highestLine[0][0]), scaleHelpers.flexCeil(xMax)]);
      });

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
      }
    };
  });
});
