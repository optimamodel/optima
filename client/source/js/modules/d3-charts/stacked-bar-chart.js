define(['d3', 'underscore'], function (d3, _) {
  'use strict';

  /**
   * Returns a StackedBarChart instance.
   */
  var StackedBarChart = function(chart, chartSize, data, colors) {

    /*
     * Returns a bar ready to render by the StackedBarChart.
     *
     * @param {array} barData - a list of the segement values. example: [22, 33]
     * @returns {array} - example: [{y0: 0, y1: 22}, {y0: 22, y1: 55}]
     */
    var generateBar = function(barData) {
      var lowerSegmentBoundary = 0;
      return _(barData).map(function(value) {
        var segment = { y0: lowerSegmentBoundary, y1: lowerSegmentBoundary + value};
        lowerSegmentBoundary = lowerSegmentBoundary + value;
        return segment;
      });
    };

    var x = d3.scale.ordinal().rangeRoundBands([0, chartSize.width], 0.1);
    var y = d3.scale.linear().rangeRound([chartSize.height, 0]);

    colors = colors || [ '__light-blue', '__blue', '__violet', '__green',
      '__light-green', '__gray', '__red' ];

    var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");

    var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left")
      .tickFormat(d3.format(".2s"));

    var chartData = _(data).map(function(entry) {
      return {
        bar: generateBar(entry[1]),
        x: entry[0]
      };
    });

    x.domain(chartData.map(function(d) { return d.x; }));
    y.domain([0, d3.max(chartData, function(d) {
      // take the largest entry from the bar
      return d.bar[d.bar.length - 1].y1;
    })]);

    chart.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + chartSize.height + ")")
      .call(xAxis);

    chart.append("g")
      .attr("class", "y axis")
      .call(yAxis)
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Population");

    var entries = chart.selectAll(".entry")
      .data(chartData)
      .enter().append("g")
      .attr("class", "entry")
      .attr("transform", function(d) { return "translate(" + x(d.x) + ",0)"; });

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

  return StackedBarChart;
});
