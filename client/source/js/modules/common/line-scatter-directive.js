define(['angular', 'd3', 'd3-box'], function (angular, d3) {
  'use strict';

  angular.module('app.line-scatter-chart', []).directive('lineScatterChart', function () {
    return {
      scope: {
        data: '='
      },
      link: function (scope, element, attrs) {
        function drawAxes(scales, labels, axesGroup) {
          var xLabel = labels['x'];
          var yLabel = labels['y'];

          var xTicks = scales.x.domain()[1] - scales.x.domain()[0] + 1;
          var xAxis = d3.svg.axis().scale(scales.x).orient("bottom").ticks(xTicks);
          var yAxis = d3.svg.axis().scale(scales.y).orient("left");

          if (axesGroup.select(".x.axis").empty()) {
            axesGroup.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + chart_size.height + ")")
              .call(xAxis);

            axesGroup.append("g")
              .attr("class", "y axis")
              .call(yAxis);

            axesGroup.select(".x.axis")
              .append("text")
              .text(xLabel)
              .attr("x", chart_size.width / 2)
              .attr("y", margins.bottom - 3)
              .attr("id", "xLabel");

            axesGroup.select(".y.axis")
              .append("text")
              .text(yLabel)
              .attr("text-anchor", "middle")
              .attr("transform", "rotate (-270, 0, 0)")
              .attr("x", chart_size.height / 2)
              .attr("y", margins.left - 3)
              .attr("id", "yLabel");
          } else {
            document.getElementById('xLabel').textContent = xLabel;
            axesGroup.select(".x.axis")
              .transition()
              .duration(transitionTimeout)
              .call(xAxis);

            document.getElementById('yLabel').textContent = yLabel;
            axesGroup.select(".y.axis")
              .transition()
              .duration(transitionTimeout)
              .call(yAxis);
          }
        }

        var dimensions = { width: 1000, height: 300 };
        var margins = { top: 10, right: 10, bottom: 35, left: 60 };
        var chart_size = {
          width: dimensions.width - margins.left - margins.right,
          height: dimensions.height - margins.top - margins.bottom
        };

        var svg = d3.select(element[0])
          .append("svg")
          .attr("width", dimensions.width)
          .attr("height", dimensions.height)
          .append("g")
          .attr("transform", "translate(" + margins.left + "," + margins.top + ")");

        // Define svg groups
        var chartGroup = svg.append("g").attr("class", "chart_group");
        var axesGroup = svg.append("g").attr("class", "axes_group");

        var boxChartInstance = new BoxChart(chartGroup, chart_size, 100);
        var lineChartInstance = new LineChart(chartGroup, chart_size, 100);
        //var scatterChartInstance = new ScatterChart(chartGroup, chart_size, 100);

        scope.data.$promise.then(function(d){
          var scatterErrorData = d['scatter-error'];
          var lineData = d['line'];

          var calculatedBoxScales = boxChartInstance.scales(scatterErrorData);
          var calculatedLineScales = lineChartInstance.scales(lineData);
          // FIXME: uncomment this
          //var calculatedScatterScales = scatterChartInstance.scales(scope.lineChartData);

          drawAxes(calculatedLineScales, { x: 'Label X', y: 'Label Y' }, axesGroup);
          boxChartInstance.draw(scatterErrorData);
          lineChartInstance.draw(lineData);
          // FIXME: uncomment this
          // scatterChartInstance.draw(lineChartData);
        });

      }
    }
  });

  /**
   * Define charts constructors
   */

  function BoxChart(chart, chart_size, transitionTimeout) {
    var xScale, yScale;

    var box_height = chart_size.height;
    var box_width = 10;
    var xPadding = box_width / 2;

    var box = d3.box()
      .whiskers(iqr(1.5))
      .width(box_width)
      .height(box_height);

    this.scales = function (dataset) {
      var xExtent = d3.extent(dataset, function (d) {
        return d[0];
      });
      xScale = d3.scale.linear().domain(xExtent).range([box_width, chart_size.width - box_width]);

      var yMax = d3.max(dataset, function (d) {
        return d[2];
      });
      yScale = d3.scale.linear().domain([0, yMax]).range([chart_size.height, 0]);

      return { x: xScale, y: yScale };
    };

    this.draw = function (dataset) {
      var min = Infinity,
        max = -Infinity;

      var data = [];
      dataset.forEach(function (x) {
        var e = Math.floor(x[0]),
          r = Math.floor(x[1]),
          s = Math.floor(x[2]),
          d = data[e];
        if (!d) d = data[e] = [s];
        else d.push(s);
        if (s > max) max = s;
        if (s < min) min = s;
      });

      box.domain([min, max]);

      //selection
      var selection = chart.selectAll("g.box").data(data);

      //add new data-join elements
      selection.enter()
        .append("g")
        .attr("class", "box")
        .attr("transform", function (d, i) {
          return "translate(" + (xScale(i) - xPadding) + ",0)"
        });

      //update data-join
      selection.call(box.duration(transitionTimeout));
    };

    this.dispose = function () {
      var selection = chart.selectAll("g.box");
      selection.call(box.domain([0, 0]));
      selection.transition().duration(transitionTimeout).remove();
    };

    // Returns a function to compute the interquartile range.
    function iqr(k) {
      return function (d, i) {
        var q1 = d.quartiles[0],
          q3 = d.quartiles[2],
          iqr = (q3 - q1) * k,
          i = -1,
          j = d.length;
        while (d[++i] < q1 - iqr);
        while (d[--j] > q3 + iqr);
        return [i, j];
      };
    }
  }

  function LineChart(chart, chart_size, transitionTimeout) {
    var xScale, yScale;

    this.scales = function (dataset) {
      var xExtent = d3.extent(dataset, function (d) {
        return d[0];
      });
      xScale = d3.scale.linear().domain(xExtent).range([0, chart_size.width]);

      var yMax = d3.max(dataset, function (d) {
        return d[1];
      });
      yScale = d3.scale.linear().domain([0, yMax]).range([chart_size.height, 0]);

      return { x: xScale, y: yScale };
    };

    this.draw = function (dataset) {
      exit(dataset);
      transition(dataset);
      enter(dataset);
    };

    this.dispose = function () {
      exit([]);
    };

    function enter(dataset) {
      //draws circles
      chart.selectAll("circle.line_chart_circle")
        .data(dataset)
        .enter()
        .append("circle")
        .attr("cx", function (d) {
          return xScale(d[0]);
        })
        .attr("cy", function (d) {
          return yScale(d[1]);
        })
        .attr("r", 0)
        .attr("class", "line_chart_circle")
        .on("mouseover", function (d) {
          var point = d3.select(this);
          point.transition().attr("r", 8);
        })
        .on("mouseout", function () {
          d3.select(this).transition().attr("r", 4);

        })
        .transition()
        .duration(transitionTimeout)
        .attr("r", 4);


      //draws path
      if (chart.select("path.line_chart_path").empty()) {
        var line = d3.svg.line()
          .x(function (d) {
            return xScale(d[0])
          })
          .y(function (d) {
            return yScale(d[1])
          });
        chart.append("path")
          .attr("d", line(dataset))
          .attr("class", "line_chart_path")
          .attr("opacity", 0)
          .transition()
          .duration(transitionTimeout)
          .attr("opacity", 1);
      }
    }

    function transition(dataset) {
      //update circles
      chart.selectAll("circle.line_chart_circle")
        .data(dataset)
        .transition()
        .duration(transitionTimeout)
        .each("start", function () {
          d3.select(this)
            .attr("class", "line_chart_circle_transition")
            .attr("r", 6);
        })
        .attr("cx", function (d) {
          return xScale(d[0]);
        })
        .attr("cy", function (d) {
          return yScale(d[1]);
        })
        .each("end", function () {
          d3.select(this)
            .transition()
            .duration(1000)
            .attr("class", "line_chart_circle")
            .attr("r", 4);
        });

      //update path
      var line = d3.svg.line()
        .x(function (d) {
          return xScale(d[0])
        })
        .y(function (d) {
          return yScale(d[1])
        });
      chart.select("path.line_chart_path")
        .transition()
        .duration(transitionTimeout)
        .attr("d", line(dataset));
    }

    function exit(dataset) {
      //removes circles
      chart.selectAll("circle.line_chart_circle")
        .data(dataset)
        .exit()
        .transition()
        .duration(transitionTimeout)
        .attr("r", 0)
        .remove();

      //removes path
      chart.select("path.line_chart_path")
        .data(dataset)
        .exit()
        .transition()
        .duration(transitionTimeout)
        .attr("opacity", 0)
        .remove();
    }
  }

  function ScatterChart(chart, chart_size, transitionTimeout) {
    var xScale, yScale;

    this.scales = function (dataset) {
      var xExtent = d3.extent(dataset, function (d) {
        return d[0];
      });
      xScale = d3.scale.linear().domain(xExtent).range([0, chart_size.width]);

      var yMax = d3.max(dataset, function (d) {
        return d[1];
      });
      yScale = d3.scale.linear().domain([0, yMax]).range([chart_size.height, 0]);

      return { x: xScale, y: yScale };
    };

    this.draw = function (dataset) {
      chart.selectAll(".dot")
        .data(dataset)
        .enter().append("circle")
        .attr("class", "dot")
        .attr("r", 3.5)
        .attr("cx", xMap)
        .attr("cy", yMap)
        .style("fill", function (d) {
          return color(cValue(d));
        })
        .on("mouseover", function (d) {
          tooltip.transition()
            .duration(200)
            .style("opacity", .9);
          tooltip.html(d["Cereal Name"] + "<br/> (" + xValue(d)
          + ", " + yValue(d) + ")")
            .style("left", (d3.event.pageX + 5) + "px")
            .style("top", (d3.event.pageY - 28) + "px");
        })
        .on("mouseout", function (d) {
          tooltip.transition()
            .duration(500)
            .style("opacity", 0);
        });
    };

    this.dispose = function () {
      exit([]);
    };
  }
});
