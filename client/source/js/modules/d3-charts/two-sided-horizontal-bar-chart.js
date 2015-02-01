define(['d3', 'underscore', './scale-helpers'], function (d3, _, scaleHelpers) {
  'use strict';

  /**
   * Returns a bar ready to render by the StackedBarChart.
   *
   * @param {array} barData - a list of the segement values. example: [22, 33]
   * @returns {array} - example: [{x0: 0, x1: 22}, {x0: 22, x1: 55}]
   */
  var generateBar = function (barData) {
    var lowerSegmentBoundary = 0;
    return _(barData).map(function(value) {
      var segment = { x0: lowerSegmentBoundary, x1: lowerSegmentBoundary + value};
      lowerSegmentBoundary = lowerSegmentBoundary + value;
      return segment;
    });
  };

  /**
   * Returns the x value of the largest bar.
   */
  var rightXMax = function (chartData) {
    return d3.max(chartData, function(d) {
      // take the largest entry from the bar
      return d.rightBar[d.rightBar.length - 1].x1;
    });
  };

  /**
   * Returns the x value of the largest bar.
   */
  var leftXMax = function (chartData) {
    return d3.max(chartData, function(d) {
      // take the largest entry from the bar
      return d.leftBar;
    });
  };

  /**
  * Returns a TwoSidedHorizontalBarCHart instance.
  */
  function TwoSidedHorizontalBarCHart (chart, chartSize, data, colors) {

    var chartData = _(data).map(function(entry) {
      return {
        rightBar: generateBar(entry[2]),
        leftBar: entry[1],
        y: entry[0]
      };
    });

    var sideWidth = chartSize.width / 2;

    var y = d3.scale.ordinal().rangeRoundBands([0, chartSize.height], 0.5);
    y.domain(chartData.map(function(d) { return d.y; }));

    var rightXScale = d3.scale.linear().rangeRound([0, sideWidth]);
    rightXScale.domain([0, scaleHelpers.flexCeil(rightXMax(chartData))]);

    var leftXScale = d3.scale.linear().rangeRound([0, sideWidth]);
    leftXScale.domain([0, scaleHelpers.flexCeil(leftXMax(chartData))]);

    /**
    * Draw the chart based on the data provided during construction.
    */
    var drawLeftBar = function (chartGroup) {
      var entries = chartGroup.selectAll(".entry")
      .data(chartData)
      .enter().append("rect")
      .attr("height", y.rangeBand())
      .attr("width", function(d) { return leftXScale(d.leftBar); })
      .attr("transform", function(d) {
        return ["translate(", sideWidth - leftXScale(d.leftBar),",", y(d.y), ")"].join(' ');
      })
      .attr("class", function(d, index) {
        return ['__color-blue-1', 'stacked-bar-chart-rect'].join(' ');
      });
    };

    /**
     * Draw the chart based on the data provided during construction.
     */
    var drawRightBar = function (chartGroup) {
      var entries = chartGroup.selectAll(".entry")
      .data(chartData)
      .enter().append("g")
      .attr("class", "entry")
      .attr("transform", function(d) {
        return ["translate(0,", y(d.y), ")"].join(' ');
      });

      entries.selectAll("rect")
      .data(function(d) { return d.rightBar; })
      .enter().append("rect")
      .attr("height", y.rangeBand())
      .attr("x", function(d) {
        return rightXScale(d.x0);
      })
      .attr("width", function(d) { return rightXScale(d.x1); })
      .attr("class", function(d, index) {
        return [colors[index], 'stacked-bar-chart-rect'].join(' ');
      });
    };

    this.draw = function () {
      var leftGroup = chart.append('g').attr('class', 'left_group');
      var rightChart = chart.append('g').attr('class', 'right_group')
        .attr("transform", function(d) {
          return ["translate(", sideWidth + 2,", 0)"].join(' ');
        });

      drawLeftBar(leftGroup);
      drawRightBar(rightChart);
    };
  }

  return TwoSidedHorizontalBarCHart;
});
