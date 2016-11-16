define(
  ['./module', 'underscore', 'jquery', 'mpld3', 'saveAs', 'jsPDF', './svg-to-png', './export-helpers-service'],
  function (module, _, $, mpld3, saveAs, jspdf, svgToPng) {

  'use strict';

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

          // we look for the background and make it opaque
          if ($path.css('fill')=="rgb(255, 255, 255)") {
            $path.css('fill', "rgba(255, 255, 255, 0)");
            $path.css('stroke', "rgba(255, 255, 255, 0)");
          }
        });

        var baseAxes = $svgFigure.find('.mpld3-baseaxes');
        baseAxes.append(pathsToCopy);
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


  module.directive('mpld3Chart', function ($http, modalService, exportHelpers) {

    return {
      scope: { chart: '=mpld3Chart' },
      templateUrl: './js/modules/charts/mpld3-chart.html',
      link: function (scope, elem, attrs) {

        var chartStylesheetUrl = './assets/css/chart.css';

        var initialize = function() {
          scope.chartType = attrs.chartType;
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

        scope.exportGraphAsSvg = function() {
          var originalStyle;
          var elementId = elem.attr('id');

          var $originalSvg = elem.parent().find('svg');
          var viewBox = $originalSvg[0].getAttribute('viewBox');
          var orginalWidth, orginalHeight;
          if (viewBox) {
            var tokens = viewBox.split(" ");
            orginalWidth = parseFloat(tokens[2]);
            orginalHeight = parseFloat(tokens[3]);
          } else {
            orginalWidth = $originalSvg.width();
            orginalHeight = $originalSvg.height();
          }

          originalStyle = 'padding: ' + $originalSvg.css('padding');
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

        scope.exportGraphAsPng = function() {
          exportHelpers.generateGraphAsPngOrJpeg(
              elem.parent(),
              function(blob) { saveAs(blob, "graph.png"); },
              'blob');
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
      templateUrl: './js/modules/charts/optima-graphs.html',
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