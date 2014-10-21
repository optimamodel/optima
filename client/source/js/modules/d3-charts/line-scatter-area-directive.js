define(['./module'], function (module) {
  'use strict';

  module.directive('lineScatterAreaChart', function (d3Charts) {
      return {
        scope: {
          data: '='
        },
        link: function (scope, element) {
          var dimensions = { width: 1000, height: 300 };
          var margins = { top: 50, right: 10, bottom: 35, left: 60 };
          var chartSize = {
            width: dimensions.width - margins.left - margins.right,
            height: dimensions.height - margins.top - margins.bottom
          };

          var svg = d3Charts.createSvg(element[0], dimensions, margins);

          // Define svg groups
          var chartGroup = svg.append("g").attr("class", "chart_group");
          var axesGroup = svg.append("g").attr("class", "axes_group");

          var lineChartInstance = new d3Charts.LineChart(chartGroup, '', chartSize, 100);
          var lineChartInstance1 = new d3Charts.LineChart(chartGroup, '_area1', chartSize, 100);
          var lineChartInstance2 = new d3Charts.LineChart(chartGroup, '_area2', chartSize, 100);
          var areaChartInstance = new d3Charts.AreaChart(chartGroup, '', chartSize, 100);
          var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize, 100);

          scope.data.$promise.then(function (d) {
            var lineData = d.line;
            var areaLine1Data = d.area.line1;
            var areaLine2Data = d.area.line2;
            var areaData = areaLine1Data.map(function(dot, index) {
              return {
                x: dot[0],
                y0: dot[1],
                y1: areaLine2Data[index][1]
              };
            });
            var scatterData = d.scatter;

            var calculatedLineScales = lineChartInstance.scales(lineData);
            lineChartInstance1.scales(lineData);
            lineChartInstance2.scales(lineData);
            areaChartInstance.scales(lineData);
            scatterChartInstance.scales(lineData);

            d3Charts.drawAxes(calculatedLineScales, { x: 'Label X', y: 'Label Y' }, axesGroup, chartSize, margins);

            areaChartInstance.draw(areaData);
            lineChartInstance1.draw(areaLine1Data);
            lineChartInstance2.draw(areaLine2Data);
            lineChartInstance.draw(lineData);
            scatterChartInstance.draw(scatterData);
          });

        }
      }
    });
});
