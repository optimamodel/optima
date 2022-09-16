define(
  ['angular', 'underscore', 'jquery', 'mpld3', 'saveAs'],
  function (angular, _, $, mpld3, saveAs, rpcService) {

  'use strict';

  /**
   * this module holds all the plotting related elements in one
   * file:
   *
   * - all the hacks to work-around mpld3 for optima graphs
   * - the directive <mpld3-chart> to display mpld3 charts, with
   *   downloading options
   * - the directive <optima-graphs> that displays a set of
   *   charts for a given result, with associated controls,
   *   and downloading options
   * - the controllers of these directives
   */

  var module = angular.module('app.charts', []);

  var moduleAllCharts, moduleScrollTop;

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
    var $textLabels = $svgFigure.find('.mpld3-baseaxes > text');

    if ($textLabels) {
      // the legend path is stored under .mpd3-axes, and needs
      // to be moved into the .mpld3-baseaxes, it's presumably
      // the last path under .mpld3-axes
      // so need to work out how many entries in legend
      // it is the the number of textlabels - title and axe labels
      // var nLegend = $textLabels.length - 3;
      var paths = $svgFigure.find('.mpld3-axes > path');

      // it looks like the legend background sneaks in as a path
      // and is not drawn in the right order

      // we extract the lines of the legend AND the background
      var pathsToCopy = paths.slice(paths.length - nLegend - 1, paths.length);

      _.each(pathsToCopy, function(path) {
        var $path = $(path);

        // we look for the background and make it opaque -- WARNING, can probably remove this
        if (($path.css('fill')=="rgb(255, 255, 255)") || ($path.css('fill')=='#ffffff')) {
          $path.css('fill-opacity', 0);
          $path.css('stroke', "none");
        }
      });

      var baseAxes = $svgFigure.find('.mpld3-baseaxes');
      baseAxes.append(pathsToCopy);
    }
  }

  function reformatMpld3FigsInElement($element, nLegend, xlabels, ylabels) {

    $element.find('svg.mpld3-figure').each(function () {
      // Match the size of the figure to the wrapping svg element
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
        // override the mouseover defaults
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

    // reformat y-ticks
    var $yaxis = $element.find('.mpld3-yaxis');
    var $labels = $yaxis.find('g.tick > text');
    var i = 0
    $labels.each(function () {
      var $label = $(this);
      var text = ylabels[i].replace(/,/g, '');  // Very hacky replacement of the ylabels that got lost in the translation in the BE (see comments !~! in the BE)
      var newText = reformatYTickStr(text);
      $label.text(newText);
      i = i + 1
    });

    // reformat x-ticks
    var $xaxis = $element.find('.mpld3-xaxis');
    var $labels = $xaxis.find('g.tick > text');
    var i = 0
    $labels.each(function () {
      var $label = $(this);
      var text = xlabels[i].replace(/,/g, ''); // Very hacky replacement of the xlabels that got lost in the translation in the BE (see comments !~! in the BE)
      var newText = reformatXTickStr(text);
      $label.text(newText);
      i = i + 1
    });
  }

  function changeWidthOfSvg(svg, width) {
    var $svg = $(svg);
    var ratio = $svg.attr('width') / $svg.attr('height');
    var height = width / ratio;
    $svg.attr('width', width);
    $svg.attr('height', height);
  }

  module.directive('mpld3Chart', function (modalService, rpcService) {

    return {
      scope: { chart: '=mpld3Chart' },
      templateUrl: './js/modules/charts/mpld3-chart.html?cacheBust=xxx',
      link: function (scope, elem, attrs) {

        var chartStylesheetUrl = './assets/css/chart.css';

        var initialize = function() {
          scope.chartType = attrs.chartType;
          scope.buttonsOff = ('buttonsOff' in attrs);
        };

        function getFigure () {
          var id = attrs.chartId;
          return _(mpld3.figures).findWhere({ figid: id })
        }

        function getZoomPlugin () {
          return _(getFigure().plugins).find(function(plugin) {
            return plugin.constructor.name === 'mpld3_BoxZoomPlugin';
          });
        }

        function disableZoomAndPan () {
          // disable zoom
          getZoomPlugin().deactivate();
          scope.zoomEnabled = false;

          // disable pan
          getFigure().toolbar.fig.disable_zoom();
          scope.panEnabled = false;
        }

        scope.resetZoomAndPanInChart = function (params) {
          params.$event.preventDefault();
          getFigure().toolbar.fig.reset();
        };

        scope.toggleZoomInChart = function (params) {
          params.$event.preventDefault();

          var zoomWasEnabled = getZoomPlugin().enabled;
          disableZoomAndPan();

          if (!zoomWasEnabled) {
            scope.zoomEnabled = true;
            getZoomPlugin().activate();
          }
        };

        scope.togglePanInChart = function (params) {
          params.$event.preventDefault();

          var panWasEnabled = getFigure().toolbar.fig.zoom_on;

          disableZoomAndPan();

          if (!panWasEnabled) {
            getFigure().toolbar.fig.enable_zoom();
            scope.panEnabled = true;
          }
        };

        scope.exportFigure = function(filetype) { /* Adding function(name) brings up save dialog box */
          var resultId = attrs.resultId;
          var graphIndex = attrs.graphIndex;
          var graphSelectorsString = attrs.graphSelectors; // graphSelectors gets converted to a string, so convert back: e.g. '["a","b"]' -> 'a, b' -> 'a','b'
          var graphSelectors = graphSelectorsString.split('"').join('').slice(1,-1).split(','); // http://stackoverflow.com/questions/19156148/i-want-to-remove-double-quotes-from-a-string
          rpcService
            .rpcDownload(
              'download_figures', [resultId, graphSelectors, filetype, parseInt(graphIndex)]);
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

            var initWidth;
            if ('initWidth' in figure) {
              initWidth = figure.initWidth;
              delete figure.initWidth;
            }

            mpld3.draw_figure(attrs.chartId, figure);
            reformatMpld3FigsInElement($element, nLegend, figure.xlabels, figure.ylabels);  // Very hacky replacement of the ylabels that got lost in the translation in the BE (see comments !~! in the BE)

            if (!_.isUndefined(initWidth)) {
              changeWidthOfSvg($element.find('svg'), initWidth);
            }

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

  module.directive('optimaGraphs', function (toastr, rpcService, RzSliderOptions) {
    return {
      scope: { 'graphs':'=' },
      templateUrl: './js/modules/charts/optima-graphs.html?cacheBust=xxx',
      link: function (scope, elem, attrs) {

        function initialize() {

          var allCharts = elem.find('.allcharts');

          scope.state = {
            slider1: {
              value: 0.48,
              options: {
                floor: 0.1,
                ceil: 1,
                step: 0.01,
                precision: 2,
                onChange: scope.changeFigWidth
              }
            },
              slider2: {
                value: 0.8,
                currentValue: 0.8, // To look at changes
                options: {
                  floor: 0.1,
                  ceil: 1,
                  step: 0.1,
                  precision: 1,
                  onEnd: scope.changeFontSize
                }
            }
          };

          moduleAllCharts = $(elem).find('.allcharts');
          moduleScrollTop = moduleAllCharts.scrollTop();
          moduleAllCharts.scroll(function() {
            moduleScrollTop = moduleAllCharts.scrollTop();
          });
        }

        scope.exportAllFigures = function(name) { /* Adding function(name) brings up save dialog box */
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          var which = scope.getSelectors();
          var index = null;
          var filetype = 'singlepdf';
          rpcService
            .rpcDownload('download_figures', [resultId, which, filetype, index]);
        };

        scope.exportAllData = function(name) { /* Adding function(name) brings up save dialog box */
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          console.log('resultId', resultId);
          rpcService
            .rpcDownload('download_result_data', [resultId]);
        };

        scope.updateGraphs = function() {
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          console.log('updateGraphs resultId', scope.graphs.resultId);
          var which = scope.getSelectors();
          var zoom = scope.state.slider2.currentValue;
          if (scope.graphs.advanced) {
            which.push("advanced");
          }
          rpcService
            .rpcRun('load_result_mpld3_graphs',
              [resultId, which, zoom])
            .then(function(response) {
              scope.graphs = response.data.graphs;
              toastr.success('Graphs updated');
            });
        };

        scope.toggleAdvanced = function() {
          scope.graphs.advanced = !scope.graphs.advanced;
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          console.log('toggleAdvanced', scope.graphs.advanced, 'resultId', scope.graphs.resultId);
          var which = scope.getSelectors();
          var zoom = scope.state.slider2.currentValue;
          if (scope.graphs.advanced) {
            which.push("advanced");
          }
          rpcService
            .rpcRun('load_result_mpld3_graphs',
              [resultId, which, zoom])
            .then(function(response) {
              scope.graphs = response.data.graphs;
              toastr.success('Graphs updated');
            });
        };

        scope.defaultGraphs = function() {  // Same as above, except don't invert advanced
          var resultId = scope.graphs.resultId;
          if (_.isUndefined(resultId)) {
            return;
          }
          console.log('defaultGraphs', scope.graphs.advanced, 'resultId', scope.graphs.resultId);
          var which = ["default"];
          if (scope.graphs.advanced) {
            which.push("advanced");
          }
          rpcService
            .rpcRun('load_result_mpld3_graphs',
              [resultId, which])
            .then(function(response) {
              scope.graphs = response.data.graphs;
              toastr.success('Graphs updated');
            });
        };

        function isChecked(iGraph) {
          var graph_selector = scope.graphs.graph_selectors[iGraph];
          var selector = _.findWhere(scope.graphs.selectors, { key: graph_selector });
          return (!_.isUndefined(selector) && (selector.checked));
        }

        function getSelectedFigureWidth() {
          var frac = scope.state.slider1.value;
          var allCharts = elem.find('.allcharts');
          var allChartsWidth = parseInt(allCharts.width());
          var width = allChartsWidth * frac; // This sets the default to be 0.48
          return width;
        }

        scope.$watch(
          'graphs',
          function() {
            if (_.isUndefined(scope.graphs)) {
              return;
            }
            if (scope.graphs) {
              var width = getSelectedFigureWidth();
              _.each(scope.graphs.mpld3_graphs, function(g, i) {
                g.isChecked = function() {
                  return isChecked(i);
                };
                g.initWidth = width;
              });
            }
          }
        );

        // WARNING -- do we need this!?
        /*scope.toggleAdvanced = function() {
          scope.switchGraphs();
        };*/

        // Or this?
        scope.defaultSelectors = function() {
          scope.defaultGraphs();
        };

        scope.clearSelectors = function() {
            _.each(scope.graphs.selectors, function (selector) {
              selector.checked = false;
            });
        };

        scope.getSelectors = function() {
          function getChecked(s) { return s.checked; }
          function getKey(s) { return s.key }
          var which = [];
          if (scope.graphs) {
            if (scope.graphs.advanced) {
              which.push('advanced');
            }
            var selectors = scope.graphs.selectors;
            if (selectors) {
              which = which.concat(_.filter(selectors, getChecked).map(getKey));
            }
          }
          return which;
        };

        // Change figure width -- called by the "Zoom" slider
        scope.changeFigWidth = function() {
          var width = getSelectedFigureWidth();
          $(elem)
            .find(".allcharts")
            .find('svg.mpld3-figure')
            .each(function(i, svg) {
              changeWidthOfSvg(svg, width);
            });
        };

        // Update the grahps, but only if the font size has actually changed -- called by the "Font" slider
        scope.changeFontSize = function() {
          if (scope.state.slider2.currentValue !== scope.state.slider2.value) {
            scope.state.slider2.currentValue = scope.state.slider2.value;
            scope.updateGraphs();
          }

        };

        initialize();
      }
    };
  });

  return module;

});
