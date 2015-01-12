define(['./module', './scale-helpers', 'angular'], function (module, scaleHelpers, angular) {
  'use strict';

  module.directive('stackedAreaChart', function (d3Charts) {
    var svg;

    var drawGraph = function (data, options, rootElement) {
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

      var colors = [ '__light-blue', '__orange', '__light-orange', '__violet',
        '__green', '__light-green', '__red', '__gray' ];


      _(data).each(function (area, index) {
        // if (index === 0) { return false }
        var areaChart = new d3Charts.AreaChart(chartGroup, chartSize, colors[index]);

        var scale = areaChart.scales(data[0]);

        var areaData = data[index].map(function (dot) {
          return {
            x: dot[0],
            y0: dot[1],
            y1: 0
          };
        });
        areaChart.draw(areaData);
      });


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
