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
        /**
         * We use the chart id to track by id in ng-repeat to avoid redrawing of all the charts when the chart array
         * is updated when resizing the charts.
         * */
        var generateChartId = function () {
          return _.uniqueId("chart_");
        };

        var resizeChart = function (chart, newWidth, newHeight) {
          var widthOffset = 20;
          var heightOffset = chart.type == 'stackedAreaChart' ? 210 : 100;
          chart.options.width = newWidth - widthOffset;
          chart.options.height = newHeight - heightOffset;
          chart.id = generateChartId();
        };

        var initialResize = true;

        /**
         * Resize all charts. The resizing is done after the gridster items are already rendered.
         */
        var resizeAllCharts = function (charts) {
          // small optimization: avoid double resizing during the initial render
          if (initialResize === true) {
            initialResize = false;
            return;
          }
          $('.chart-container').each(function (index, chartContainer) {
            var newWidth = $(chartContainer).outerWidth();
            var newHeight = $(chartContainer).outerHeight();
            // happens when removing the chart
            if (index < charts.length) {
              var chart = charts[index];
              resizeChart(chart, newWidth, newHeight);
            }
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
            // configure the gridster items
            var rows = 5, cols = 4;
            scope.$watch('charts', function (charts) {
              _(charts).each(function (chart, index) {
                var row = Math.floor(index / cols) * rows, col = (index % cols) * cols;
                chart.gridsterItem = {sizeX: cols, sizeY: rows, row: row, col: col, index: index};
                chart.id = generateChartId();
              });
              resizeAllCharts(charts);
            });

            /** When the window or gridster element are resized */
            scope.$on('gridster-resized', function () {
              resizeAllCharts(scope.charts);
            });

            scope.gridsterOpts = {
              columns: 16,
              margins: [10, 10],
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
                  resizeChart(chart, newWidth, newHeight);
                  // shallow copy instead of deep copy with angular.copy
                  scope.charts[widget.index] = _.clone(chart);
                }
              }
            };
          }
        };
      });
});
