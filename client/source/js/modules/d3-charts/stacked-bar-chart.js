define(['d3', 'underscore', './scale-helpers'], function (d3, _, scaleHelpers) {
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

  /**
   * Returns the y value of the largest bar.
   */
  var yMax = function (chartData) {
    return d3.max(chartData, function(d) {
      // take the largest entry from the bar
      return d.bar[d.bar.length - 1].y1;
    });
  };

  /**
   * Returns a scale only having entries which have 50px distance to each other.
   *
   * This helper function is needed for ordinal scales which are very close.
   * Without filtering out labels the x-axis labels would overlap.
   */
  var generateAxisScale = function(baseScale, chartData) {

    // no need to filter the scale if there is only one entry
    if (chartData.length < 2) { return baseScale; }

    var barWidth = baseScale(chartData[1].x) - baseScale(chartData[0].x);

    // we only want to take every x element to have enough space between the ticks
    // If a bar is one pixel only every 50 tick is shown. If the bars are wider
    // more ticks can be added by a factor of the barWidth
    var skipXElements = Math.ceil(50 / barWidth);

    var newScale = d3.scale.ordinal();

    var xValues = _.chain(chartData)
      .map(function(item) { return scaleHelpers.flexCeil(item.x); })
      .filter(function(item, index) { return index % skipXElements === 0;})
      .value();

    var xRangeValues = _.chain(baseScale.range())
      .filter(function(x, index) { return index % skipXElements === 0;})
      // 2x 0.5 because we take half of the bar & the padding which is 0.5 of bar
      .map(function(x) { return Math.ceil(x + barWidth * 0.5 * 0.5); })
      .value();

    // add line start & end to make sure the axis is drawn from beginning to end
    xValues.unshift('');
    xRangeValues.unshift(baseScale.rangeExtent()[0]);
    xValues.push('');
    xRangeValues.push(baseScale.rangeExtent()[1]);

    newScale.domain(xValues);
    newScale.range(xRangeValues);


    return newScale;
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

    var x = d3.scale.ordinal().rangeRoundBands([0, chartSize.width], 0.5);
    x.domain(chartData.map(function(d) { return d.x; }));

    var y = d3.scale.linear().rangeRound([chartSize.height, 0]);
    y.domain([0, scaleHelpers.flexCeil(yMax(chartData))]);

    /**
     * Returns an object containing x & y functions for scaling the axis.
     */
    this.axisScales = function () {
      return { x: generateAxisScale(x, chartData), y: y };
      // return { x: x, y: y };
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
