define(['d3', 'underscore'], function (d3, _) {
  'use strict';

  /**
   * Returns a bar ready to render by the StackedBarChart.
   *
   * @param {array} barData - a list of the segement values. example: [22, 33]
   * @returns {array} - example: [{y0: 0, y1: 22}, {y0: 22, y1: 55}]
   */
  var generateBar = function (barData) {
    var lowerSegmentBoundary = 0;
    return _(barData).map(function(value) {
      var segment = { y0: lowerSegmentBoundary, y1: lowerSegmentBoundary + value};
      lowerSegmentBoundary = lowerSegmentBoundary + value;
      return segment;
    });
  };

  var yMax = function (chartData) {
    return d3.max(chartData, function(d) {
      // take the largest entry from the bar
      return d.bar[d.bar.length - 1].y1;
    });
  };

  /**
   * Returns a StackedBarChart instance.
   */
  function StackedBarChart (chart, chartSize, data, colors) {

    var chartData = _(data).map(function(entry) {
      return {
        bar: generateBar(entry[1]),
        x: entry[0]
      };
    });

    var x = d3.scale.ordinal().rangeRoundBands([0, chartSize.width], 0.1);
    var y = d3.scale.linear().rangeRound([chartSize.height, 0]);
    x.domain(chartData.map(function(d) { return d.x; }));
    y.domain([0, yMax(chartData)]);

    /**
     * Returns an object containing x & y functions for scaling.
     */
    this.scales = function () {
      return { x: x, y: y };
    };

    /**
     * Returns the highest point of all bars.
     */
    this.yMax = function () {
      return yMax(chartData);
    };

    /**
     * Draw the chart based on the data provided during construction.
     */
    this.draw = function () {
      var entries = chart.selectAll(".entry")
        .data(chartData)
        .enter().append("g")
        .attr("class", "entry")
        .attr("transform", function(d) {
          return ["translate(", x(d.x), ",0)"].join(' ');
        });

      entries.selectAll("rect")
        .data(function(d) { return d.bar; })
        .enter().append("rect")
        .attr("width", x.rangeBand())
        .attr("y", function(d) { return y(d.y1); })
        .attr("height", function(d) { return y(d.y0) - y(d.y1); })
        .attr("class", function(d, index) {
          return [colors[index], 'stacked-bar-chart-rect'].join(' ');
        });
    };
  }

  return StackedBarChart;
});
