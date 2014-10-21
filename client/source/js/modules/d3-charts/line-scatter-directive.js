define(['./module'], function (module) {
  'use strict';

  module.directive('lineScatterChart', function (d3Charts) {
    return {
      scope: {
        data: '='
      },
      link: function (scope, element) {
        var dimensions = { width: 1000, height: 300 };
        var margins = { top: 10, right: 10, bottom: 35, left: 60 };
        var chartSize = {
          width: dimensions.width - margins.left - margins.right,
          height: dimensions.height - margins.top - margins.bottom
        };

        var svg = d3Charts.createSvg(element[0], dimensions, margins);

        // Define svg groups
        var chartGroup = svg.append("g").attr("class", "chart_group");
        var axesGroup = svg.append("g").attr("class", "axes_group");

        var lineChartInstance = new d3Charts.LineChart(chartGroup, '', chartSize, 100);
        var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize, 100);

        scope.data.$promise.then(function(d){
          var scatterErrorData = d['scatter-error'];
          var lineData = d.line;

          var calculatedLineScales = lineChartInstance.scales(lineData);
          scatterChartInstance.scales(lineData);

          d3Charts.drawAxes(calculatedLineScales, { x: 'Label X', y: 'Label Y' }, axesGroup, chartSize, margins);
          lineChartInstance.draw(lineData);
          scatterChartInstance.draw(scatterErrorData);
        });

      }
    }
  });
});
