define(
    ['./module', 'underscore', 'jquery', 'mpld3', 'saveAs', 'jsPDF',
      './svg-to-png', './export-helpers-service'],
    function (module, _, $, mpld3, saveAs, jspdf, svgToPng) {

  'use strict';

  var moduleAllCharts, moduleScrollTop;

  function consoleLogJson(name, val) {
    console.log(name + ' = ');
    console.log(JSON.stringify(val, null, 2));
  }


  function val2str(val, limit, suffix) {
    var reducedVal = val / limit;
    var leftOver = reducedVal % 1.0;
    var nDecimal = 0;
    if (leftOver > 0.05) {
      nDecimal = 1;
    }
    return "" + reducedVal.toFixed(nDecimal) + suffix;
  }


  function reformatXTickStr(text) {
    var val = parseFloat(text);
    if (val >= 1E9) {
      text = val2str(val, 1E9, 'b')
    } else if (val >= 1E6) {
      text = val2str(val, 1E6, 'm')
    } else if (val >= 3E3) {
      text = val2str(val, 1E3, 'k')
    }
    return text;
  }


  function reformatYTickStr(text) {
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


  function addLineToLegendLabel($svgFigure, nLegend) {
      // add lines in legend labels
      var $textLabels = $svgFigure.find('.mpld3-baseaxes > text');
      if ($textLabels) {
        // the legend path is stored under .mpd3-axes, and needs
        // to be moved into the .mpld3-baseaxes, it's presumably
        // the last path under .mpld3-axes
        // so need to work out how many entries in legend
        // it is the the number of textlabels - title and axe labels
        // var nLegend = $textLabels.length - 3;
        var $paths = $svgFigure.find('.mpld3-axes > path');
        var $pathsToCopy = $paths.slice($paths.length - nLegend, $paths.length);
        var $baseAxes = $svgFigure.find('.mpld3-baseaxes');
        $baseAxes.append($pathsToCopy);
      }
  }

  function reformatMpld3FigsInElement($element, nLegend) {
    $element.find('svg.mpld3-figure').each(function () {
      var $svgFigure = $(this);
      var width = $svgFigure.attr('width');
      var height = $svgFigure.attr('height');
      var ratio = width / height;
      $svgFigure[0].setAttribute('viewBox', '0 0 ' + width + ' ' + height);
      var width = $svgFigure.parent().width();
      var height = width / ratio;
      $svgFigure.attr('width', width);
      $svgFigure.attr('height', height);

      $svgFigure.on('mouseover', function () {
        var height = parseInt($svgFigure.attr('height'));
        $svgFigure.find('.mpld3-coordinates').each(function () {
          $(this).attr('top', height + 7);
        });
        $svgFigure.find('.mpld3-toolbar').each(function () {
          $(this).remove();
        });
      });

      addLineToLegendLabel($svgFigure, nLegend);
    });

    var $yaxis = $element.find('.mpld3-yaxis');
    var $labels = $yaxis.find('g.tick > text');
    $labels.each(function () {
      var $label = $(this);
      var text = $label.text().replace(/,/g, '');
      var newText = reformatYTickStr(text);
      $label.text(newText);
    });

    var $xaxis = $element.find('.mpld3-xaxis');
    var $labels = $xaxis.find('g.tick > text');
    $labels.each(function () {
      var $label = $(this);
      var text = $label.text().replace(/,/g, '');
      var newText = reformatXTickStr(text);
      $label.text(newText);
    });
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
          var viewBox = $originalSvg[0].getAttribute('viewBox');
          var orginalWidth, orginalHeight;
          if (viewBox) {
            // console.log('viewbox', viewBox);
            var tokens = viewBox.split(" ");
            orginalWidth = parseFloat(tokens[2]);
            orginalHeight = parseFloat(tokens[3]);
          } else {
            orginalWidth = $originalSvg.width();
            orginalHeight = $originalSvg.height();
          }

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

            if (_.isUndefined(figure.axes)) {
              return;
            }

            // clear element before stuffing a figure in there
            var $element = $(elem).find('.mpld3-chart').first();
            $element.attr('id', attrs.chartId);
            $element.html("");

            // calculates the number of items in the legend
            // to be used in the hack to fix the lines appearing
            // in legend. this assumes that any text labels appearing
            // in the right side of the figure (x > 0.7) is a legend
            // label and thus gives the number of items in the
            // legend. this will be used to transfer the paths
            // for the legened into the right DOM element in
            // addLineToLegendLabel
            var nLegend = 0;
            _.each(figure.axes[0].texts, function(text) {
              var position = text.position;
              if (parseFloat(position[0]) > 0.7) {
                nLegend += 1;
              }

              // ensure y-axis label is not too far from axis
              if (parseFloat(position[0]) < 0) {
                position[0] = -0.2;
              }

              // ensure x-axis label is not too far from axis
              if ((parseFloat(position[1]) < 0) && (parseFloat(position[0]) < 0.7)) {
                position[1] = -0.3;
              }
            });

            mpld3.draw_figure(attrs.chartId, figure);
            reformatMpld3FigsInElement($element, nLegend);

            if (!_.isUndefined(moduleAllCharts)) {
              moduleAllCharts.scrollTop(moduleScrollTop);
            }
          },
          true
        );

        initialize();

      }
    };
  });

  module.directive('optimaGraphs', function ($http, toastr) {
    return {
      scope: { 'graphs':'=' },
      templateUrl: './js/modules/mpld3-charts/optima-graphs.html',
      link: function (scope, elem, attrs) {

        function initialize() {
          scope.state = {
            slider: {
              value: 400,
              options: {
                floor: 200,
                ceil: 1300,
                onChange: scope.changeFigWidth
              }
            }
          };

          moduleAllCharts = $(elem).find('.allcharts');
          moduleScrollTop = moduleAllCharts.scrollTop();
          moduleAllCharts.scroll(function() {
            moduleScrollTop = moduleAllCharts.scrollTop();
          });
        }

        scope.exportAllData = function() {
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          console.log('resultId', resultId);
          $http.get(
            '/api/results/' + resultId,
            {
              headers: {'Content-type': 'application/octet-stream'},
              responseType: 'blob'
            })
          .success(function (response) {
            var blob = new Blob([response], { type: 'text/csv;charset=utf-8' });
            saveAs(blob, ('export_graphs.csv'));
          });
        };

        function getSelectors() {
          if (scope.graphs) {
            function getChecked(s) { return s.checked; }
            function getKey(s) { return s.key }
            var selectors = scope.graphs.selectors;
            if (selectors) {
              var which = _.filter(selectors, getChecked).map(getKey);
              console.log('which', which);
              if (which.length > 0) {
                return which;
              }
            }
          }
          return null;
        }

        scope.updateGraphs = function() {
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          $http.post(
            '/api/results/' + resultId,
            {which: getSelectors()})
          .success(function (response) {
            scope.graphs = response.graphs;
            toastr.success('Graphs updated');
          });
        };

        function isChecked(iGraph) {
          var graph_selector = scope.graphs.graph_selectors[iGraph];
          var selector = _.findWhere(scope.graphs.selectors, { key: graph_selector });
          return (!_.isUndefined(selector) && (selector.checked));
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
          }
        );

        scope.clearSelectors = function() {
            _.each(scope.graphs.selectors, function (selector) {
              selector.checked = false;
            });
        };

        scope.changeFigWidth = function() {
          function setAllFiguresToWidth($element) {
            var $figures = $element.find('svg.mpld3-figure');
            $figures.each(function() {
              var $svgFigure = $(this);
              var ratio = $svgFigure.attr('width') / $svgFigure.attr('height');
              var width = scope.state.slider.value;
              var height = width / ratio;
              $svgFigure.attr('width', width);
              $svgFigure.attr('height', height);
            });
          }
          setAllFiguresToWidth($(elem).find(".allcharts"));
        };

        initialize();
      }
    };
  });

});
