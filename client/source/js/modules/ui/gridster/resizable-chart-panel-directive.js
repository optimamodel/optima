define(['./module', 'underscore'], function (module, _) {
  /**
   * Adds a gridster directive to the element.
   *
   * The grid setup is a 16 column setup with 5x4 (5 rows 4 cols) per item and
   * is currently not customizable. The directive applies appropriate chart resizing
   * specific to stackedAreaCharts and lineAreaScatterCharts.
   *
   * The current setup should be extended to be more customizable as use cases expand.
   */
  return module
      .directive('resizableChartPanel', function () {
        // configure the gridster items
        var rows = 5, cols = 4, columns = 16, margin = 10;

        /**
         * We use the chart id to track by id in ng-repeat to avoid redrawing of all the charts when the chart array
         * is updated when resizing the charts.
         * */
        var generateChartId = function () {
          return _.uniqueId("chart_");
        };

        function getHeightOffset(chart){
          return chart.type == 'stackedAreaChart' ? 210 : 100;
        }

        var resizeChart = function (chart, colWidth) {
          var widthOffset = 20;
          var heightOffset = chart.type == 'stackedAreaChart' ? 210 : 100;
          chart.options.width = chart.gridsterItem.sizeX * colWidth - widthOffset;
          chart.id = generateChartId();
        };

        var initialResize = true;

        /**
         * Resize all charts. The resizing is done after the gridster items are already rendered.
         */
        var resizeAllCharts = function (charts, colWidth) {
          // small optimization: avoid double resizing during the initial render
          if (!colWidth) {
            return;
          }
          angular.forEach(charts,function(chart, index) {
            var row = Math.floor(index / cols) * rows, col = (index % cols) * cols;

            chart.gridsterItem = {
              sizeX: cols,
              sizeY: Math.ceil((chart.options.height + getHeightOffset(chart))/colWidth),
              row: row,
              col: col,
              index: index};
            chart.id = generateChartId();
            resizeChart(chart, colWidth);
          });
          // shallow copy instead of deep copy with angular.copy
          // trigger a change for the surrounding repeater
          if (charts.length > 0)
            charts[0] = _.clone(charts[0]);
        };

        return {
          template: '<div gridster="gridsterOpts"><ng-transclude></ng-transclude></div>',
          transclude: true,
          restrict: 'A',
          scope: {
            charts: "=resizableChartPanel"
          },
          link: function (scope, element) {

            angular.forEach(scope.charts,function(chart) {
              chart.id=generateChartId();
            });
            scope.$watch('charts', function (charts) {
              resizeAllCharts(charts, scope.currentColumnWidth);
            });

            /** When the window or gridster element are resized */
            scope.$on('gridster-resized', function (event, widths) {
              scope.currentColumnWidth = (widths[0]- margin )/columns;
              resizeAllCharts(scope.charts, scope.currentColumnWidth);
            });

            scope.gridsterOpts = {
              columns: columns,
              margins: [margin, margin],
              resizable: {
                // item finished resizing
                stop: function (event, $element, widget) {
                  /**
                   * Use the '.gridster-preview-holder' instead '.chart-container' like in resizeCharts(),
                   * because while resizing the '.chart-container' width/height changing and are not yet final
                   */
                  var previewHolder = $('.gridster-preview-holder');
                  var newWidth = previewHolder.width();
                  var newHeight = previewHolder.height();
                  var chart = scope.charts[widget.index];
                  chart.options.width = newWidth - 2 * margin;
                  chart.options.height = newHeight - getHeightOffset(chart);
                  chart.id=generateChartId();
                  // shallow copy instead of deep copy with angular.copy
                  scope.charts[widget.index] = _.clone(chart);
                }
              }
            };
          }
        };
      });
});
