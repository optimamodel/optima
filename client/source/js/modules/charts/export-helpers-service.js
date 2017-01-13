define(['angular', 'jquery', './svg-to-png', 'underscore'], function (angular, $, svgToPng, _) {
  'use strict';

  return angular
      .module('app.charts.export-helpers',[])
      .factory('exportHelpers', ['$http', function ($http) {

    var chartCssUrl = '/assets/css/chart.css';

    /**
     * Generate an image out of a SVG graph
     *
     * In order to achieve this a new SVG is created including styles.
     * This SVG element is used as data source inside an image which then
     * is used to draw the content on a canvas to save it as PNG.
     *
     * @param {element} el - DOM element containing the chart.
     * @param {function} callback - DOM element containing the chart.
     * @param {string} [type] - for 'blob' a PNG blob is returned, if undefined
     *                          a string of JPEG image data is returned
     */
    var generateGraphAsPngOrJpeg = function( el, callback, type ) {

      var elementId = $(el).find('[mpld3-chart]').attr('id');
      var $originalSvg = el.find('svg');
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
      var originalStyle = $originalSvg.attr('style') || '';
      var scalingFactor = 4.2;

      // in order to have styled graphs the css content used to render
      // graphs is retrieved & inject it into the svg as style tag
      var cssContentRequest = $http.get(chartCssUrl);
      cssContentRequest.success(function(chartStylesheetContent) {

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

        // make sure we scale the padding and append it to the original styling
        // info: later declarations overwrite previous ones
        var svgInlineStyle = originalStyle + '; background:#fff; ' + svgToPng.scalePaddingStyle($originalSvg, scalingFactor);

        // create svg element
        var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, svgInlineStyle, elementId);

        // add styles and content to the svg
        var styles = '<style>' + styleContent + '</style>';
        svg.innerHTML = styles + $originalSvg.html();

        // create img element with the svg as data source
        var svgXML = (new XMLSerializer()).serializeToString(svg);
        var tmpImage = document.createElement("img");
        tmpImage.width = orginalWidth * scalingFactor;
        tmpImage.height = orginalHeight * scalingFactor;
        tmpImage.src = "data:image/svg+xml;charset=utf-8,"+ svgXML;
        // console.log(svgXML);
        tmpImage.onload = function() {
          // draw image into canvas in order to convert it to a blob
          var canvas = document.createElement("canvas");
          canvas.width = orginalWidth * scalingFactor;
          canvas.height = orginalHeight * scalingFactor;
          var ctx = canvas.getContext("2d");
          ctx.drawImage(tmpImage, 0, 0);

          // Return the png either as a blob or data url
          if ( type == 'blob' ) {
            canvas.toBlob( callback );
          } else {
            var data = canvas.toDataURL('image/jpeg', 0.7);
            callback( data );
          }
        };
      }).error(function() {
        alert("Please releod and try again, something went wrong while generating the graph.");
      });
    };

    return {
      generateGraphAsPngOrJpeg: generateGraphAsPngOrJpeg
    };
  }]);
});
