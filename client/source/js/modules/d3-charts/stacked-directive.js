define(['./module', './scale-helpers', 'angular'], function (module, scaleHelpers, angular) {
  'use strict';

  module.directive('stackedChart', function (d3Charts) {
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

      // Define svg groups
      var chartGroup = svg.append('g').attr('class', 'chart_group');
      var axesGroup = svg.append('g').attr('class', 'axes_group');
      var headerGroup = svg.append('g').attr('class', 'header_group');

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
