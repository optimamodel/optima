define(['./module'], function (module) {
  'use strict';

  module.directive('pieChart', function (d3Charts) {
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

      var chartSize = {
        width: options.width - options.margin.left - options.margin.right,
        height: options.height - options.margin.top - options.margin.bottom
      };

      svg = d3Charts.createSvg(rootElement[0], dimensions, options.margin);
      var parentGroup = svg.append("g").attr("class","parent_group");

      // Define svg groups
      var chartGroup = parentGroup.append('g').attr('class', 'chart_group');
      var headerGroup = parentGroup.append('g').attr('class', 'header_group');

      d3Charts.PieChart(chartGroup, chartSize, data.slices, svg);
      d3Charts.drawTitleAndLegend(svg, options, headerGroup);
    };

    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {

        scope.$watchCollection('[data,options]', function() { // before this change, all the graphs were redrawn three times
          drawGraph(scope.data, angular.copy(scope.options), element);
        });
      }
    };
  });
});
