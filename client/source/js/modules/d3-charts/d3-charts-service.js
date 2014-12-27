define(['./module', 'd3'], function (module, d3) {
  'use strict';

  module.service('d3Charts', function () {

    // available colors, see .line in _chart.scss
    var colors = [ '__orange', '__light-orange', '__violet', '__green', '__light-green', '__red', '__gray' ];

    function LineChart(chart, lineIndex, chartSize, customColor) {
      var xScale, yScale;

      var uniqClassName = 'line' + lineIndex;
      var lineColor = customColor || colors[lineIndex];

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
        if (chart.select('path.' + uniqClassName).empty()) {
          var line = d3.svg.line()
            .interpolate('basis')
            .x(function (d) {
              return xScale(d[0]);
            })
            .y(function (d) {
              return yScale(d[1]);
            });

          chart.append('path')
            .attr('d', line(dataset))
            .attr('class', 'line ' + lineColor + ' ' + uniqClassName);
        }
      }

      function transition(dataset) {
        //update path
        var line = d3.svg.line()
          .x(function (d) {
            return xScale(d[0]);
          })
          .y(function (d) {
            return yScale(d[1]);
          });
        chart.select('path.' + uniqClassName)
          .attr('d', line(dataset));
      }

      function exit(dataset) {
        //removes path
        chart.select('path.' + uniqClassName)
          .data(dataset)
          .exit()
          .remove();
      }
    }

    function AreaChart(chart, suffix, chart_size) {
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
          .remove();
      }
    }

    function ScatterChart(chart, suffix, chartSize) {
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
          .attr('class', className)
          .attr('r', 4);
      }

      function transition(dataset) {
        chart.selectAll('circle.' + className)
          .data(dataset)
          .attr('cx', function (d) {
            return xScale(d[0]);
          })
          .attr('cy', function (d) {
            return yScale(d[1]);
          })
          .attr('r', 4);
      }

      function exit(dataset) {
        //removes circles
        chart.selectAll('circle.' + className)
          .data(dataset)
          .exit()
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
        .ticks(Math.floor(chartSize.width / 50)); // one tick per 50 pixels

      var yAxis = d3.svg.axis()
        .scale(scales.y)
        .tickFormat(options.yAxis.tickFormat)
        .orient('left');

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
        .attr('y', options.margin.bottom - 3);

      axesGroup.select('.y.axis')
        .append('text')
        .text(yLabel)
        .attr('text-anchor', 'middle')
        .attr('transform', 'rotate (-90, 0, 0)')
        .attr('x', -chartSize.height / 2)
        .attr('y', -options.margin.left + 17);

      if (options.hasTitle) {
        axesGroup.append('text')
          .attr('class', 'graph-title')
          .text(options.title)
          .attr('y', - (options.margin.top - 20));

        // wrap text nodes to fit width
        enableTextWrap(axesGroup.select('.graph-title'), options.width - options.margin.left - options.margin.right);
      }

      if (options.hasLegend) {
        var graphLegend = axesGroup.append('g')
          .attr('class', 'graph-legend');

        options.legend.forEach(function (legendItem, index) {
          var item = graphLegend.append('g')
            .attr('class', 'graph-legend_i');

          var y = - (options.margin.top - 50 - index * 15);

          item.append('text')
            .attr('class', 'graph-legend_text')
            .attr('y', y)
            .text(legendItem.title);

          item.append('circle')
            .attr('class', 'graph-legend_dot line ' + (legendItem.color || colors[index]))
            .attr('r', 4)
            .attr('cy', y - 4)
            .attr('cx', -10);

          // wrap text nodes to fit width
          enableTextWrap(axesGroup.select('.graph-legend_text'), options.width - options.margin.left - options.margin.right - 10);
        });
      }
    }

    function enableTextWrap (text, width) {
      text.each(function() {
        var text = d3.select(this),
          words = text.text().split(/\s+/).reverse(),
          word,
          line = [],
          lineNumber = 0,
          lineHeight = 1.1, // ems
          y = text.attr('y'),
          dy = parseFloat(text.attr('dy')) || 0,
          tspan = text.text(null).append('tspan')
            .attr('x', 0)
            .attr('y', y)
            .attr('dy', dy + 'em');
        while (word = words.pop()) {
          line.push(word);
          tspan.text(line.join(' '));
          if (tspan.node().getComputedTextLength() > width) {
            line.pop();
            tspan.text(line.join(' '));
            line = [word];
            tspan = text.append('tspan')
              .attr('x', 0)
              .attr('y', y)
              .attr('dy', ++lineNumber * lineHeight + dy + 'em')
              .text(word);
          }
        }
      });
    }

    function adaptOptions (options) {
      options.hasTitle = !!options.title;
      options.hasLegend = !!options.legend;

      var offset = 0;
      if (options.hasTitle) {
        offset += 30;
      }

      if (options.hasLegend) {
        offset += 50;
      }

      options.margin.top += offset;
      options.height += offset;

      // if there are custom colors - attach colors to legend
      if (options.legend) {
        var hasCustomColors = options.linesStyle;

        options.legend = _(options.legend).map(function (title, index) {
          var item = {
            title: title
          };

          if (hasCustomColors) {
            item.color = options.linesStyle[index];
          }

          return item;
        });
      }

      return options;
    }

    function createSvg(element, dimensions, margins) {
      return d3.select(element)
        .append('svg')
        .attr('width', dimensions.width)
        .attr('height', dimensions.height)
        .append('g')
        .attr('transform', 'translate(' + margins.left + ',' + margins.top + ')');
    }

    return {
      adaptOptions: adaptOptions,
      createSvg: createSvg,
      drawAxes: drawAxes,
      enableTextWrap: enableTextWrap,
      AreaChart: AreaChart,
      LineChart: LineChart,
      ScatterChart: ScatterChart
    };
  });
});
