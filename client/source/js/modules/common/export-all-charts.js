define(['angular', 'jquery', 'underscore', 'jsPDF', './export-helpers-service'],
function (angular, $, _, jspdf) {
  'use strict';

  return angular.module('app.export-all-charts', ['app.common.export-helpers'])
  .directive('exportAllCharts', function ($http, modalService, exportHelpers) {
    return {
      restrict: 'E',
      scope: {
        name: '@',
        customTitles: '='
      },
      template: '<button type="button" class="btn" ng-click="exportAllFigures()">Export all figures</button>',
      link: function (scope, elem, attrs) {

        /**
        * Export all graphs/charts figures,
        */
        scope.exportAllFigures = function () {
          var totalElements = $(".chart-container").length;

          // Start the pdf document
          var doc = new jspdf('landscape', 'pt', 'a4', true);

          // Set font
          doc.setFont( 'helvetica', 'bold' );
          doc.setFontSize( 16 );

          _( $(".chart-container") ).each(function ( el, index ) {

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
              if (scope.customTitles) {
                centeredText(doc, scope.customTitles[index], startingY);
              }

              if ( index == totalElements - 1 ) {
                doc.save(scope.name + '.pdf');
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
