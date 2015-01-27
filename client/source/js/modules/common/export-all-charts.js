define(['angular', 'jquery', 'underscore', 'jsPDF', './export-helpers-service'],
function (angular, $, _, JsPdf) {
  'use strict';

  return angular.module('app.export-all-charts', ['app.common.export-helpers'])
  .directive('exportAllCharts', function ($q, $http, modalService, exportHelpers) {
    return {
      restrict: 'E',
      scope: {
        name: '@',
        customTitles: '='
      },
      template: '<button type="button" class="btn" ng-click="exportAllFigures()">Export all figures</button>',
      link: function (scope, elem, attrs) {

        /**
         * Helper function to add a centered text to a certain document.
         *
         * @param {object} doc - a JsPdf to which the text should be added.
         * @param {string} text - the text do be added
         * @param {number} y - the y position of the current page in the doc
         */
        var centeredText = function(doc, text, y) {
          var textWidth = doc.getStringUnitWidth(text) * doc.internal.getFontSize() / doc.internal.scaleFactor;
          var textOffset = (doc.internal.pageSize.width - textWidth) / 2;
          doc.text(textOffset, y, text);
        };

        /**
         * Export all charts figures in pdf document
         */
        scope.exportAllFigures = function () {
          var totalElements = $(".chart-container").length;

          // Start the pdf document
          var doc = new JsPdf('landscape', 'pt', 'a4', true);

          // Set font
          doc.setFont( 'helvetica', 'bold' );
          doc.setFontSize( 16 );

          // to guarantee the correct order we store all image data in an array
          // and only when all data is avaialble we generate the PDF document
          var generateGraphPromises = [];

          _( $(".chart-container") ).each(function ( el, index ) {

            var graphDeferred = new $.Deferred();
            generateGraphPromises[index] = graphDeferred.promise();

            var figureWidth = $(el).find('svg').outerWidth() * 1.4;
            var figureHeight = $(el).find('svg').outerHeight() * 1.4;
            var graph = {
              imageData: undefined,
              figureWidth: figureWidth,
              figureHeight: figureHeight,
              startingX: (842 - figureWidth) / 2,
              startingY: (595 - figureHeight) / 2
            };

            // Generate a png of the graph and save it into an array to be used
            // to generate the pdf.
            exportHelpers.generateGraphAsPngOrJpeg( $(el), function( data ) {
              graph.imageData = data;
              graphDeferred.resolve(graph);
            }, 'data-url' );
          });

          $.when.apply($, generateGraphPromises).done(function() {
            _(arguments).each(function(graph, index) {

              // Add image
              doc.addImage(graph.imageData, 'JPEG', graph.startingX,
                graph.startingY, graph.figureWidth, graph.figureHeight);

              // Image title
              if (scope.customTitles) {
                centeredText(doc, scope.customTitles[index], graph.startingY);
              }

              if ( index == totalElements - 1 ) {
                doc.save(scope.name + '.pdf');
              } else {
                doc.addPage();
              }
            });
          });
        };
      }
    };
  });
});
