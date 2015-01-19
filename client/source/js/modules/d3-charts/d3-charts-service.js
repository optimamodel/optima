define(['./module', 'd3', 'underscore', './scale-helpers'], function (module, d3, _, scaleHelpers) {
  'use strict';

  module.service('d3Charts', function () {



    /**
     * Returns a PieChart instance.
     *
     * Data has to be provided in the following format: {label: "xxzy", value: 44}
     */
    function PieChart(chart, chartSize, data) {
      var radius = Math.min(chartSize.width, chartSize.height) / 2;

      var color = d3.scale.ordinal()
        .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

      var arc = d3.svg.arc()
       .outerRadius(radius - 10)
       .innerRadius(0);

      var pie = d3.layout.pie()
       .sort(null)
       .value(function(d) { return d.value; });

      chart.attr("transform", "translate(" + chartSize.width / 2 + "," + chartSize.height / 2 + ")");

      var g = chart.selectAll(".arc")
        .data(pie(data))
        .enter().append("g")
        .attr("class", "arc");

      g.append("path")
        .attr("d", arc)
        .style("fill", function(d) { return color(d.data.label); });

      g.append("text")
        .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .text(function(d) { return d.data.label; });
    }


    /**
     * Returns a LineChart instance.
     *
     * @param {element} chart - element where to append the line.
     * @param {object} chartSize - example: { width: 200, height: 100 }.
     * @param {string} colorClass - see available colors in chart/_color.scss.
     */
    function LineChart(chart, chartSize, colorClass) {
      var xScale, yScale;

      var uniqClassName = _.uniqueId('line_');

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
            .attr('class', ['line ', colorClass, uniqClassName].join(' '));
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

    /**
     * Returns a AreaChart instance.
     *
     * @param {element} chart - element where to append the line.
     * @param {object} chartSize - example: { width: 200, height: 100 }.
     * @param {string} colorClass - see available colors in chart/_color.scss.
     */
    function AreaChart(chart, chartSize, colorClass) {
      var xScale, yScale;

      var className = 'area_chart_path';
      var uniqClassName = _.uniqueId('area_chart_path');

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
          var area = d3.svg.area()
            .interpolate('basis')
            .x(function(d) { return xScale(d.x); })
            .y0(function(d) { return yScale(d.y0); })
            .y1(function(d) { return yScale(d.y1); });

          chart.append('path')
            .attr('d', area(dataset))
            .attr('class', [className, uniqClassName, colorClass].join(' '));
        }
      }

      function transition(dataset) {
      }

      function exit(dataset) {
        //removes path
        chart.select('path.' + uniqClassName)
          .data(dataset)
          .exit()
          .remove();
      }
    }

    /**
     * Returns a ScatterChart instance.
     *
     * @param {element} chart - element where to append the line.
     * @param {object} chartSize - example: { width: 200, height: 100 }.
     */
    function ScatterChart(chart, chartSize) {
      var xScale, yScale,
        className = 'scatter_chart_circle';

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
      scales.x.domain([Math.floor(domain[0]), scaleHelpers.flexCeil(domain[1])]);

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
        .attr('y', 35);

      axesGroup.select('.y.axis')
        .append('text')
        .text(yLabel)
        .attr('text-anchor', 'middle')
        .attr('transform', 'rotate (-90, 0, 0)')
        .attr('x', -chartSize.height / 2)
        .attr('y', -options.margin.left + 17);
    }

    function drawTitleAndLegend (svg, options, headerGroup) {
      var titleOffsetTop = 20;

      if (options.hasTitle) {
        var titleWidth = options.width - options.margin.left - options.margin.right;

        headerGroup.append('text')
          .attr('class', 'graph-title')
          .text(options.title)
          .attr('y', - (options.margin.top - titleOffsetTop));

        // wrap text nodes to fit width
        enableTextWrap(headerGroup.select('.graph-title'), titleWidth);
      }

      var legendHeight = 0,
        legendLines = 0,
        legendLineHeight = 15,
        legendWidth = options.width - options.margin.left - options.margin.right - 10,
        legendOffsetTop = 15;

      if (options.hasLegend) {
        var graphLegend = headerGroup.append('g')
          .attr('class', 'graph-legend')
          .attr('transform', 'translate(0,' + (options.height - options.margin.bottom + legendOffsetTop) + ')');

        _(options.legend).each(function (legendItem, index) {
          var item = graphLegend.append('g')
            .attr('class', 'graph-legend_i');

          var y = legendLines * legendLineHeight;

          var text = item.append('text')
            .attr('class', 'graph-legend_text')
            .attr('y', y)
            .text(legendItem.title);

          item.append('circle')
            .attr('class', 'graph-legend_dot line ' + (legendItem.color))
            .attr('r', 4)
            .attr('cy', y - 4)
            .attr('cx', -10);

          // wrap text nodes to fit width
          legendLines += enableTextWrap(text, legendWidth);
        });

        legendHeight = legendOffsetTop + legendLines * legendLineHeight;
      }

      // update svg height and padding to make sure that legend is visible
      setSvgHeightAndPadding(svg,
        options.height + legendHeight,
        [options.margin.top, options.margin.right, options.margin.bottom, options.margin.left]
      );
    }

    /**
     * Enables SVG text wrapping
     * http://bl.ocks.org/mbostock/7555321
     *
     * @param text SVG text element
     * @param width to wrap to
     *
     * @return number of lines created
     */
    function enableTextWrap (text, width) {
      var words = text.text().split(/\s+/).reverse(),
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
      return lineNumber + 1;
    }

    /**
     * If there is a title for graph it'll increase graph height,
     * if there is a legend provided it'll map legend labels array into an object - with title and color
     *
     * @param options
     * @returns {*}
     */
    function adaptOptions (options) {
      options.hasTitle = !!options.title;
      options.hasLegend = !!options.legend;

      var titleOffset = 0;
      if (options.hasTitle) {
        titleOffset += 30;
      }
      options.margin.top += titleOffset;
      options.height += titleOffset;

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
      var svg = d3.select(element)
        .append('svg')
        .attr('width', dimensions.width);

      setSvgHeightAndPadding(svg, dimensions.height, [margins.top, margins.right, margins.bottom, margins.left]);
      return svg;
    }

    /**
     * @param svg
     * @param height
     * @param padding - array of padding values [top, right, bottom, left]
     */
    function setSvgHeightAndPadding (svg, height, padding) {
      svg.attr('height', height)
        .attr('style', 'padding:' + padding.join('px ') + 'px');
    }

    return {
      adaptOptions: adaptOptions,
      createSvg: createSvg,
      drawAxes: drawAxes,
      drawTitleAndLegend: drawTitleAndLegend,
      enableTextWrap: enableTextWrap,
      setSvgHeightAndPadding: setSvgHeightAndPadding,
      AreaChart: AreaChart,
      LineChart: LineChart,
      ScatterChart: ScatterChart,
      PieChart: PieChart
    };
  });
});
