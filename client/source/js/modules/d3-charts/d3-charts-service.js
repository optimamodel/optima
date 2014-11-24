define(['./module', 'd3', 'd3-box'], function (module, d3) {
  'use strict';

  module.service('d3Charts', function () {

    function LineChart(chart, suffix, chartSize, transitionTimeout) {
      var xScale, yScale;

      var className = 'line_chart_path' + suffix;

      this.scales = function (dataset) {
        var xExtent = d3.extent(dataset, function (d) {
          return d[0];
        });
        xScale = d3.scale.linear().domain(xExtent).range([0, chartSize.width]);

        var yMax = d3.max(dataset, function (d) {
          return d[1];
        });
        yScale = d3.scale.linear().domain([0, yMax]).range([chartSize.height, 0]);

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
        //draws path
        if (chart.select('path.' + className).empty()) {
          var line = d3.svg.line()
            .interpolate('basis')
            .x(function (d) {
              return xScale(d[0])
            })
            .y(function (d) {
              return yScale(d[1])
            });

          chart.append('path')
            .attr('d', line(dataset))
            .attr('class', className)
            .attr('opacity', 0)
            .transition()
            .duration(transitionTimeout)
            .attr('opacity', 1);
        }
      }

      function transition(dataset) {
        //update circles
        chart.selectAll('circle.line_chart_circle')
          .data(dataset)
          .transition()
          .duration(transitionTimeout)
          .each('start', function () {
            d3.select(this)
              .attr('class', 'line_chart_circle_transition')
              .attr('r', 6);
          })
          .attr('cx', function (d) {
            return xScale(d[0]);
          })
          .attr('cy', function (d) {
            return yScale(d[1]);
          })
          .each('end', function () {
            d3.select(this)
              .transition()
              .duration(1000)
              .attr('class', className)
              .attr('r', 4);
          });

        //update path
        var line = d3.svg.line()
          .x(function (d) {
            return xScale(d[0]);
          })
          .y(function (d) {
            return yScale(d[1]);
          });
        chart.select('path.' + className)
          .transition()
          .duration(transitionTimeout)
          .attr('d', line(dataset));
      }

      function exit(dataset) {
        //removes circles
        chart.selectAll('circle.line_chart_circle')
          .data(dataset)
          .exit()
          .transition()
          .duration(transitionTimeout)
          .attr('r', 0)
          .remove();

        //removes path
        chart.select('path.' + className)
          .data(dataset)
          .exit()
          .transition()
          .duration(transitionTimeout)
          .attr('opacity', 0)
          .remove();
      }
    }

    function AreaChart(chart, suffix, chart_size, transitionTimeout) {
      var xScale, yScale;

      var className = 'area_chart_path' + suffix;

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
        //draws path
        if (chart.select('path.' + className).empty()) {
          var area = d3.svg.area()
            .interpolate('basis')
            .x(function(d) { return xScale(d.x); })
            .y0(function(d) { return yScale(d.y0); })
            .y1(function(d) { return yScale(d.y1); });

          chart.append('path')
            .attr('d', area(dataset))
            .attr('class', className);
        }
      }

      function transition(dataset) {
      }

      function exit(dataset) {
        //removes path
        chart.select('path.' + className)
          .data(dataset)
          .exit()
          .transition()
          .duration(transitionTimeout)
          .attr('opacity', 0)
          .remove();
      }
    }

    function ScatterChart(chart, suffix, chartSize, transitionTimeout) {
      var xScale, yScale,
        className = 'scatter_chart_circle' + suffix;

      this.scales = function (dataset) {
        var xExtent = d3.extent(dataset, function (d) {
          return d[0];
        });
        xScale = d3.scale.linear()
          .domain(xExtent)
          .range([0, chartSize.width]);

        var yMax = d3.max(dataset, function (d) { return d[1]; });

        yScale = d3.scale.linear()
          .domain([0, yMax])
          .range([chartSize.height, 0]);

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
        chart.selectAll('circle.' + className)
          .data(dataset)
          .enter()
          .append('circle')
          .attr('cx', function (d) {
            return xScale(d[0]);
          })
          .attr('cy', function (d) {
            return yScale(d[1]);
          })
          .attr('r', 0)
          .attr('class', className)
          .on('mouseover', function (d) {
            var point = d3.select(this);
            point.transition().attr('r', 6);
          })
          .on('mouseout', function () {
            d3.select(this).transition().attr('r', 4);
          })
          .transition()
          .duration(transitionTimeout)
          .attr('r', 4);
      }

      function transition(dataset) {
        chart.selectAll('circle.' + className)
          .data(dataset)
          .transition()
          .duration(transitionTimeout)
          .each('start', function () {
            d3.select(this)
              .attr('class', className + '_transition')
              .attr('r', 6);
          })
          .attr('cx', function (d) {
            return xScale(d[0]);
          })
          .attr('cy', function (d) {
            return yScale(d[1]);
          })
          .each('end', function () {
            d3.select(this)
              .transition()
              .duration(1000)
              .attr('class', className)
              .attr('r', 4);
          });
      }

      function exit(dataset) {
        //removes circles
        chart.selectAll('circle.' + className)
          .data(dataset)
          .exit()
          .transition()
          .duration(transitionTimeout)
          .attr('r', 0)
          .remove();
      }
    }

    function drawAxes(scales, options, axesGroup, chartSize) {
      var xLabel = options.xAxis.axisLabel;
      var yLabel = options.yAxis.axisLabel;

      var domain = scales.x.domain();
      scales.x.domain([Math.ceil(domain[0]), Math.ceil(domain[1])]);

      var xAxis = d3.svg.axis()
        .scale(scales.x)
        .tickFormat(options.xAxis.tickFormat)
        .orient('bottom')
        .ticks(Math.floor(chartSize.width / 50));

      var yAxis = d3.svg.axis()
        .scale(scales.y)
        .tickFormat(options.yAxis.tickFormat)
        .orient('left');

      if (axesGroup.select('.x.axis').empty()) {
        axesGroup.append('g')
          .attr('class', 'x axis')
          .attr('transform', 'translate(0,' + chartSize.height + ')')
          .call(xAxis);

        axesGroup.append('g')
          .attr('class', 'y axis')
          .call(yAxis);

        axesGroup.select('.x.axis')
          .append('text')
          .text(xLabel)
          .attr('x', chartSize.width / 2)
          .attr('y', options.margin.bottom - 3)
          .attr('id', 'xLabel');

        axesGroup.select('.y.axis')
          .append('text')
          .text(yLabel)
          .attr('text-anchor', 'middle')
          .attr('transform', 'rotate (-270, 0, 0)')
          .attr('x', chartSize.height / 2)
          .attr('y', options.margin.left - 3)
          .attr('id', 'yLabel');
      } else {
        document.getElementById('xLabel').textContent = xLabel;
        axesGroup.select('.x.axis')
          .transition()
          .duration(transitionTimeout)
          .call(xAxis);

        document.getElementById('yLabel').textContent = yLabel;
        axesGroup.select('.y.axis')
          .transition()
          .duration(transitionTimeout)
          .call(yAxis);
      }
    }

    function createSvg(element, dimensions, margins) {
      return d3.select(element)
        .append("svg")
        .attr("width", dimensions.width)
        .attr("height", dimensions.height)
        .append("g")
        .attr("transform", "translate(" + margins.left + "," + margins.top + ")");
    }

    return {
      createSvg: createSvg,
      drawAxes: drawAxes,
      AreaChart: AreaChart,
      LineChart: LineChart,
      ScatterChart: ScatterChart
    };
  });
});
