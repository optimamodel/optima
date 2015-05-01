define(['angular', 'jquery', 'mpld3', 'underscore', 'saveAs', 'jsPDF', './svg-to-png', './export-helpers-service'],
  function (angular, $, mpld3, _, saveAs, jspdf, svgToPng) {
  'use strict';

  return angular.module('app.chart-toolbar', [])
    .directive('chartToolbar', function ($http, modalService, exportHelpers) {
      return {
        restrict: 'E',
        templateUrl: '/js/modules/common/chart-toolbar.html',
        replace:true,
        scope: true,
        link: function (scope, elem, attrs) {
          var chartStylesheetUrl = '/assets/css/chart.css';

          /**
           * Initializes the directive.
           */
          var initialize = function() {
            scope.chartType = attrs.chartType;
          };

          scope.exportFigure = function (params) {
            params.$event.preventDefault();

            modalService.choice(
              exportGraphAsSvg, // first button callback
              exportGraphAsPng, // second button callback
              'Download as SVG', // first button text
              'Download as PNG', // second button text
              'Please choose your preferred format', // modal message
              'Export figure' // modal title
            );
          };

          scope.exportData = function (params) {
            params.$event.preventDefault();

            if (_(attrs).has('mpld3ChartData')) {
              var mpld3Chart = scope.$eval(attrs.mpld3ChartData);
              scope.exportMpld3From(mpld3Chart);
            } else {
              var chartAccessor = attrs.d3ChartData.replace(new RegExp('.data$'), '');
              var chart = scope.$eval(chartAccessor);
              scope.exportFrom(chart);
            }
          };

          scope.resetChart = function (params) {
            params.$event.preventDefault();

            var id = attrs.chartId;
            var figure = _(mpld3.figures).findWhere({ figid: id });
            if (figure) {
              figure.toolbar.fig.reset();
            }
          };

          scope.zoomChart = function (params) {
            params.$event.preventDefault();

            var id = attrs.chartId;
            var figure = _(mpld3.figures).findWhere({ figid: id });

            if (figure) {
              var zoomPlugin = _(figure.plugins).find(function(plugin) {
                return plugin.constructor.name === 'mpld3_BoxZoomPlugin';
              });
              if (zoomPlugin.enabled) {
                scope.zoomEnabled = false;
                zoomPlugin.deactivate();
              } else {
                scope.zoomEnabled = true;
                zoomPlugin.activate();
              }
            }
          };

          scope.moveChart = function (params) {
            params.$event.preventDefault();

            var id = attrs.chartId;
            var figure = _(mpld3.figures).findWhere({ figid: id });
            if (figure) {
              figure.toolbar.fig.toggle_zoom();
              scope.moveEnabled = figure.toolbar.fig.zoom_on;
            }
          };

          /**
           * Initialize a download of the graph as SVG
           *
           * In this function the original SVG is enhanced by injecting styling.
           */
          var exportGraphAsSvg = function() {
            var originalStyle;
            var elementId = elem.attr('id');
            var isMpld3 = elementId && elementId.indexOf('mpld3') != -1;

            var $originalSvg = elem.parent().find('svg');
            var orginalWidth = $originalSvg.width();
            var orginalHeight = $originalSvg.height();
            if (isMpld3) {
              originalStyle = 'padding: ' + $originalSvg.css('padding');
            } else {
              originalStyle = $originalSvg.attr('style');
            }
            var scalingFactor = 1;

            // In order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var chartStylesheetRequest = $http.get(chartStylesheetUrl, { cache: true });
            chartStylesheetRequest.success(function(chartStylesheetContent) {

              // It is needed to fetch all as mpld3 injects multiple style tags into the DOM
              var $styleTagContentList = $('style').map(function(index, style) {
                var styleContent = $(style).html();
                if (styleContent.indexOf('div#' + elementId) != -1) {
                  return styleContent.replace(/div#/g, '#');
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

            }).error(function() {
              alert("Please reload and try again, something went wrong while generating the graph.");
            });
          };

          /**
           * Initializes a download of the graph as PNG
           */
          var exportGraphAsPng = function() {
            exportHelpers.generateGraphAsPngOrJpeg( elem.parent(), function(blob) {
              saveAs(blob, "graph.png");
            }, 'blob' );
          };

          /**
           * Requesting a Spreadsheet from the prepared dataset.
           */
          var exportApiRequest = function(title, exportableData) {
            $http({url:'/api/project/export',
                  method:'POST',
                  data: exportableData,
                  headers: {'Content-type': 'application/json'},
                  responseType:'arraybuffer'})
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

          initialize();
        }
      };
    });

});
