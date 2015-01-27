define(['angular', 'jquery', 'underscore', 'saveAs', 'jsPDF', './svg-to-png', './export-helpers-service'],
  function (angular, $, _, saveAs, jspdf, svgToPng) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function ($http, modalService, exportHelpers) {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
          var chartCssUrl = '/assets/css/chart.css';

          /**
           * Initializes the directive by appending the html and setting up the
           * event handlers.
           */
          var initialize = function() {
            var template = '<div class="chart-buttons btn-group">' +
            '<button class="btn figure">Export figure</button>' +
            '<button class="btn data">Export data</button>' +
            '</div>';

            var buttons = angular.element(template);
            // append export buttons
            elem.after(buttons);

            // setup click handlers for the different actions
            buttons
              .on('click', '.figure', function (event) {
                event.preventDefault();

                modalService.choice(
                  exportGraphAsSvg, // first button callback
                  exportGraphAsPng, // second button callback
                  'Download as SVG', // first button text
                  'Download as PNG', // second button text
                  'Please choose your preferred format', // modal message
                  'Export figure' // modal title
                );
              })
              .on('click', '.data', function (event) {
                event.preventDefault();
                //a big ugly hack to distinguish between cost and covariance graphs.
                //they are both in the same ng-repeat scope :-(
                var target = {};
                if ( attrs.variant == "radarChart" ) {
                  target = scope.radarChart;
                } else if (attrs.variant == 'pieChart') {
                  target = scope.pieChart;
                } else if (attrs.variant == 'coGraph') {
                  target = scope.coGraph;
                } else if (attrs.variant == 'ccGraph') {
                  target = scope.ccGraph;
                } else {
                  target = scope.chart;
                }

                scope.exportFrom(target);
              });
          };

          /**
           * Initialize a download of the graph as SVG
           *
           * In this function the original SVG is enhanced by injecting styling.
           */
          var exportGraphAsSvg = function() {
            var originalSvg = elem.parent().find('svg');
            var orginalWidth = originalSvg.width();
            var orginalHeight = originalSvg.height();
            var originalStyle = originalSvg.attr('style');
            var scalingFactor = 1;

            // in order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var cssContentRequest = $http.get(chartCssUrl);
            cssContentRequest.success(function(cssContent) {

              // create svg element
              var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, originalStyle);

              // add styles and content to the svg
              var styles = '<style>' + cssContent + '</style>';
              svg.innerHTML = styles + originalSvg.html();

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
           * Exports the data of the graph in the format returned by the API
           */
          scope.exportFrom = function (graphOrUndefined){
            if(!graphOrUndefined) { return exportHelpers.saySorry();}
            var exportable = exportHelpers.getExportableFrom(graphOrUndefined);

            if(exportable === null) { return exportHelpers.saySorry(); }
            var title = graphOrUndefined.options.title || 'Data';
            $http({url:'/api/project/export',
                  method:'POST',
                  data: exportable,
                  headers: {'Content-type': 'application/json'},
                  responseType:'arraybuffer'})
              .success(function (response, status, headers, config) {
                  var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                  // The saveAs function must be wrapped in a setTimeout with 0 ms because Angular has a problem with fileSaver.js on FF 34.0 and the download doesn't start
                  setTimeout(function() {
                    saveAs(blob, (title+'.xlsx'));
                  }, 0);
              })
              .error(function () {});
          };

          initialize();
        }
      };
    });

});
