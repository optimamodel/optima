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

    var axeSpacing = 4;
    var labelSpace = 120;
    // take away 4 pixel to have space for the y-axe
    var sideWidth = (chartSize.width - axeSpacing - labelSpace) / 2;

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
      .attr("width", function(d) { return rightXScale(d.x1) - rightXScale(d.x0); })
      .attr("class", function(d, index) {
        return [colors[index], 'stacked-bar-chart-rect'].join(' ');
      });
    };

    var drawAxe = function (axeGroup) {
      axeGroup.append("line")
        .style("stroke", "black")
        .attr("x1", 2)
        .attr("y1", 0)
        .attr("x2", 2)
        .attr("y2", chartSize.height);
    };

    var drawTitles = function (axeGroup, rightGroup) {
      axeGroup.append('text')
        .text("asdasd")
        .attr('x', -10)
        .attr('class', 'graph-title')
        .attr('style', 'text-anchor: end');
      rightGroup.append('text')
        .text("lalal aal")
        .attr('x', 10)
        .attr('class', 'graph-title')
        .attr('style', 'text-anchor: start');
      };

    var drawLabels = function (labelsGroup) {
      var entries = labelsGroup.selectAll(".entry")
      .data(chartData)
      .enter().append("text")
      .text(function(d) { return d.y; })
      .attr('class', 'axis')
      .attr("transform", function(d) {
        return ["translate(10,", y(d.y) + y.rangeBand(), ")"].join(' ');
      });
    };

    this.draw = function () {
      var leftGroup = chart.append('g').attr('class', 'left_group');
      var axeGroup = chart.append('g').attr('class', 'axe_group')
        .attr("transform", function(d) {
          return ["translate(", sideWidth,", 0)"].join(' ');
        });
      var rightGroup = chart.append('g').attr('class', 'right_group')
        .attr("transform", function(d) {
          return ["translate(", sideWidth + axeSpacing,", 0)"].join(' ');
        });
      var labelsGroup = chart.append('g').attr('class', 'labels_group')
        .attr("transform", function(d) {
          return ["translate(", sideWidth + axeSpacing + sideWidth,", 0)"].join(' ');
        });


      drawLeftBar(leftGroup);
      drawAxe(axeGroup);
      drawRightBar(rightGroup);
      drawTitles(axeGroup, rightGroup);
      drawLabels(labelsGroup);
    };
  }

  return TwoSidedHorizontalBarCHart;
});
