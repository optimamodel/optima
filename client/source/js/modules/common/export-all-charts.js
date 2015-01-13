define(['angular', 'jquery', 'underscore', 'jsPDF', './export-helpers-service'],
function (angular, $, _, jspdf) {
  'use strict';

  return angular.module('app.export-all-charts', ['app.common.export-helpers'])
  .directive('exportAllCharts', function ($http, modalService, exportHelpers) {
    return {
      restrict: 'E',
      scope: {
        exportCharts: '='
      },
      template: '<button class="btn" ng-click="exportAllFigures()">Export all figures</button>',
      link: function (scope, elem, attrs) {

        /**
        * Export all graphs/charts figures,
        */
        scope.exportAllFigures = function () {
          var totalElements = $(".chart-container").length;

          // Get details of all graphs.
          var graphs = exportHelpers.getCharts(scope);

          // Start the pdf document
          var doc = new jspdf('landscape', 'pt', 'a4', true);

          // Set font
          doc.setFont( 'helvetica', 'bold' );
          doc.setFontSize( 16 );

          _( $(".chart-container") ).each(function ( el, index ) {

            // FIXME: This is a hack for the case of cost coverage. We need to add the titles.
            // All other graph figures have self-contained titles.
            var graphTitle = '';
            if ( scope.exportCharts.controller == 'ModelCostCoverage') {
              if ( index === 0 ) {
                graphTitle = graphs[index].title;
              } else {
                graphTitle = graphs[Math.ceil(index / 2)].title;
              }
            }

            // Generate a png of the graph and save it into an array to be used
            // to generate the pdf.
            exportHelpers.generateGraphAsPngOrJpeg( $(el), function( data ) {
              var figureWidth = $(el).find('svg').outerWidth() * 1.4;
              var figureHeight = $(el).find('svg').outerHeight() * 1.4;
              var startingX = (842 - figureWidth) / 2;
              var startingY = (595 - figureHeight) / 2;

              // Add image
              doc.addImage(data, 'JPEG', startingX, startingY, figureWidth, figureHeight);

              var centeredText = function(doc, text, y) {
                var textWidth = doc.getStringUnitWidth(text) * doc.internal.getFontSize() / doc.internal.scaleFactor;
                var textOffset = (doc.internal.pageSize.width - textWidth) / 2;
                doc.text(textOffset, y, text);
              };

              // Image title
              centeredText(doc, graphTitle, startingY);

              if ( index == totalElements - 1 ) {
                doc.save(scope.exportCharts.name + '.pdf');
              } else {
                doc.addPage();
              }
            }, 'data-url' );
          });
        };
      }
    };
  });
});
