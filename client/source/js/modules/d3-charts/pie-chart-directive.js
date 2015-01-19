define(['./module'], function (module) {
  'use strict';

  module.directive('pieChart', function (d3Charts) {
    var svg;

    var drawGraph = function (data, options, rootElement) {
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

      // Define svg groups
      var chartGroup = svg.append('g').attr('class', 'chart_group');
      var headerGroup = svg.append('g').attr('class', 'header_group');

      d3Charts.PieChart(chartGroup, dimensions, data);
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
