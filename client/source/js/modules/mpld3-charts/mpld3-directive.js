define(
    ['./module', 'underscore', 'jquery', 'mpld3', 'saveAs', 'jsPDF', './svg-to-png', './export-helpers-service'],
    function (module, _, $, mpld3, saveAs, jspdf, svgToPng) {

  'use strict';


  function consoleLogJson(name, val) {
    console.log(name + ' = ');
    console.log(JSON.stringify(val, null, 2));
  }


  function val2str(val, limit, suffix) {
    var reducedVal = val / limit;
    var nDecimal = reducedVal >= 1 ? 0 : 1;
    return "" + reducedVal.toFixed(nDecimal) + suffix;
  }


  function reformatValStr(text) {
    var val = parseFloat(text);
    if (val >= 1E9) {
      text = val2str(val, 1E9, 'b')
    } else if (val >= 1E6) {
      text = val2str(val, 1E6, 'm')
    } else if (val >= 1E3) {
      text = val2str(val, 1E3, 'k')
    }
    return text;
  }


  function reformatFigure($figure) {
    var $yaxis = $figure.find('.mpld3-yaxis');
    var $labels = $yaxis.find('g.tick > text');
    $labels.each(function () {
      var $label = $(this);
      var text = $label.text().replace(/,/g, '');
      var newText = reformatValStr(text);
      $label.text(newText);
    });

    $figure.find('svg.mpld3-figure').each(function () {
      var $svgFigure = $(this);

      // move mouse-over to bottom right corner
      $svgFigure.on('mouseover', function () {
        var height = parseInt($svgFigure.attr('height'));
        $svgFigure.find('.mpld3-coordinates').each(function () {
          $(this).attr('y', height + 7);
        });
        $svgFigure.find('.mpld3-toolbar').each(function () {
          $(this).remove();
        });
      });

      // add lines in legend labels
      var $axesLabels = $svgFigure.find('.mpld3-baseaxes > text');
      if ($axesLabels) {
        var nLegendLabels = $axesLabels.length - 2;
        var $paths = $svgFigure.find('.mpld3-axes > path');
        var $pathsToCopy = $paths.slice($paths.length - nLegendLabels, $paths.length);
        $svgFigure.find('.mpld3-baseaxes').append($pathsToCopy);
      }
    })
  }


  module.directive(
      'mpld3Chart',
      function ($http, modalService, exportHelpers, projectApiService) {

    return {
      scope: { chart: '=mpld3Chart' },
      templateUrl: './js/modules/mpld3-charts/mpld3-chart.html',
      link: function (scope, elem, attrs) {

        var chartStylesheetUrl = './assets/css/chart.css';

        var initialize = function() {
          scope.chartType = attrs.chartType;
        };

        function getFigure () {
          var id = attrs.chartId;
          return _(mpld3.figures).findWhere({ figid: id })
        }

        // scope.exportFigure = function (params) {
        //   params.$event.preventDefault();
        //
        //   modalService.choice(
        //     exportGraphAsSvg, // first button callback
        //     exportGraphAsPng, // second button callback
        //     'Download as SVG', // first button text
        //     'Download as PNG', // second button text
        //     'Please choose your preferred format', // modal message
        //     'Export figure' // modal title
        //   );
        // };

        // /**
        //  * Exports the data of this chart as xls file format and triggers the
        //  * download.
        //  */
        // scope.exportData = function (params) {
        //   params.$event.preventDefault();
        //
        //   if (scope.chart) {
        //     scope.exportMpld3From(scope.chart);
        //   } else {
        //     var chartAccessor = attrs.d3ChartData.replace(new RegExp('.data$'), '');
        //     var chart = scope.$eval(chartAccessor);
        //     scope.exportFrom(chart);
        //   }
        // };
        //

        /**
         * Returns the mpld3 figure of this chart.
         */
        /**
         * Returns the zoomPlugin of the mpdl3 figure of this chart.
         */
        function getZoomPlugin () {
          return _(getFigure().plugins).find(function(plugin) {
            return plugin.constructor.name === 'mpld3_BoxZoomPlugin';
          });
        }

        /**
         * Disable both the zoom and the pan button.
         */
        function resetButtons () {
          // disable zoom
          getZoomPlugin().deactivate();
          scope.zoomEnabled = false;

          // disable pan
          getFigure().toolbar.fig.disable_zoom();
          scope.panEnabled = false;
        }

        /**
         * Resets zoom & pan to its initial state.
         */
        scope.resetChart = function (params) {
          params.$event.preventDefault();

          getFigure().toolbar.fig.reset();
        };

        /**
         * Toggle the zoom functionality on the chart.
         *
         * Reseting all the other buttons as well to ensure that none of them
         * are enabled at the same time.
         */
        scope.zoomChart = function (params) {
          params.$event.preventDefault();

          var zoomWasEnabled = getZoomPlugin().enabled;
          resetButtons();

          if (!zoomWasEnabled) {
            scope.zoomEnabled = true;
            getZoomPlugin().activate();
          }
        };

        /**
         * Toggle the pan functionality on the chart.
         *
         * Reseting all the other buttons as well to ensure that none of them
         * are enabled at the same time.
         */
        scope.panChart = function (params) {
          params.$event.preventDefault();

          var panWasEnabled = getFigure().toolbar.fig.zoom_on;

          resetButtons();

          if (!panWasEnabled) {
            getFigure().toolbar.fig.enable_zoom();
            scope.panEnabled = true;
          }
        };

        /**
         * Initialize a download of the graph as SVG
         *
         * In this function the original SVG is enhanced by injecting styling.
         */
        scope.exportGraphAsSvg = function() {
          var originalStyle;
          var elementId = elem.attr('id');
          var isMpld3 = elementId && elementId.indexOf('mpld3') != -1;

          var $originalSvg = elem.parent().find('svg');
          var orginalWidth = $originalSvg.width();
          var orginalHeight = $originalSvg.height();

          originalStyle = 'padding: ' + $originalSvg.css('padding');
          // if (scope.chartType === 'mpld3') {
          //   originalStyle = 'padding: ' + $originalSvg.css('padding');
          // } else {
          //   originalStyle = $originalSvg.attr('style');
          // }
          var scalingFactor = 1;

          // In order to have styled graphs the css content used to render
          // graphs is retrieved & inject it into the svg as style tag
          var chartStylesheetRequest = $http.get(chartStylesheetUrl, { cache: true });
          chartStylesheetRequest
            .success(function(chartStylesheetContent) {
              // It is needed to fetch all as mpld3 injects multiple style tags into the DOM
              var $styleTagContentList = $('style').map(function(index, style) {
                var styleContent = $(style).html();
                if (styleContent.indexOf('div#' + elementId) != -1) {
                  return styleContent.replace(/div#/g, '#');
                } else {
                  return styleContent;
                }
              });

              var styleContent = $styleTagContentList.get().join('\n');
              styleContent = styleContent + '\n' + chartStylesheetContent;

              // create svg element
              var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, originalStyle, elementId);

              // add styles and content to the svg
              var styles = '<style>' + styleContent + '</style>';
              svg.innerHTML = styles + $originalSvg.html();

              // create img element with the svg as data source
              var svgXML = (new XMLSerializer()).serializeToString(svg);
              saveAs(new Blob([svgXML], { type: 'image/svg' }), 'graph.svg');

            })
            .error(function() {
              alert("Please reload and try again, something went wrong while generating the graph.");
            });
        };

        /**
         * Initializes a download of the graph as PNG
         */
        scope.exportGraphAsPng = function() {
          exportHelpers.generateGraphAsPngOrJpeg(
              elem.parent(),
              function(blob) { saveAs(blob, "graph.png"); },
              'blob');
        };

        /**
         * Requesting a Spreadsheet from the prepared dataset.
         */
        var exportApiRequest = function(title, exportableData) {
          projectApiService.exportProject(exportableData)
            .success(function (response, status, headers, config) {
                var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                // The saveAs function must be wrapped in a setTimeout with 0 ms because Angular has a problem with fileSaver.js on FF 34.0 and the download doesn't start
                setTimeout(function() {
                  saveAs(blob, (title+'.xlsx'));
                }, 0);
            });
        };

        /**
         * Exports the data of a mpld3 graph.
         */
        scope.exportMpld3From = function (chart){
          if(!chart) {
            modalService.inform(undefined, undefined, "Sorry, this chart cannot be exported");
            return;
          }

          var exportable = exportHelpers.getMpld3ExportableFrom(chart);

          if(exportable === null) {
            modalService.inform(undefined, undefined, "Sorry, this chart cannot be exported");
            return;
          }

          var title = chart.title || 'Data';
          exportApiRequest(title, exportable);
        };

        /**
         * Exports the data of the graph in the format returned by the API
         */
        scope.exportFrom = function (graphOrUndefined){
          if(!graphOrUndefined) {
            modalService.inform(undefined, undefined, "Sorry, this chart cannot be exported");
            return;
          }

          var exportable = exportHelpers.getExportableFrom(graphOrUndefined);

          if(exportable === null) {
            modalService.inform(undefined, undefined, "Sorry, this chart cannot be exported");
            return;
          }

          var title = graphOrUndefined.options.title || 'Data';
          exportApiRequest(title, exportable);
        };

        scope.$watch(
          'chart',
          function () {
            // strip $$hashKey from ng-repeat
            var figure = angular.copy(scope.chart);
            delete figure.isChecked;

            var $element = $(elem).find('.mpld3-chart').first();
            $element.attr('id', attrs.chartId);
            $element.html("");
            mpld3.draw_figure(attrs.chartId, figure);

            reformatFigure($element);
          },
          true
        );

        initialize();

      }
    };
  });


  module.directive('optimaGraphs', function () {
    return {
      scope: { 'graphs':'=' },
      templateUrl: './js/modules/mpld3-charts/optima-graphs.html',
      link: function (scope, elem, attrs) {

        function isChecked(iGraph) {
          var graph_selector = scope.graphs.graph_selectors[iGraph];
          var selector = _.findWhere(scope.graphs.selectors, { key: graph_selector });
          if (!_.isUndefined(selector) && (selector.checked)) {
            return true;
          };
          return false;
        }

        scope.$watch(
          'graphs',
          function() {
            if (_.isUndefined(scope.graphs)) {
              return;
            }
            _.each(scope.graphs.mpld3_graphs, function (g, i) {
              g.isChecked = function () { return isChecked(i); };
            });
            var parent = $(elem).parent();
            scope.height = parent.height();
          }
        );

        scope.onResize = function () {
          var parent = $(elem).parent();
          scope.height = parent.height();
          // console.log("resize", parent, scope.height);
          scope.$apply();
        };

        $(window).bind('resize', function () {
          scope.onResize();
        })
      }
    };
  });

});
