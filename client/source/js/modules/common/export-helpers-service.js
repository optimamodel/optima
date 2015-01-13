define(['angular', 'jquery', './svg-to-png'], function (angular, $, svgToPng) {
  'use strict';

  return angular.module('app.common.export-helpers',[])
  .factory('exportHelpers', ['$http', function ($http) {

    var chartCssUrl = '/assets/css/chart.css';

    /**
    * Get the graph as a PNG.
    *
    * In order to achieve this a new SVG is created including styles.
    * This SVG element is used as data source inside an image which then
    * is used to draw the content on a canvas to save it as PNG.
    */
    var generateGraphAsPngOrJpeg = function( el, callback, type ) {
      var originalSvg = el.find('svg');
      var orginalWidth = $(originalSvg).outerWidth();
      var orginalHeight = $(originalSvg).outerHeight();
      var originalStyle = originalSvg.attr('style');
      var scalingFactor = 4.2;

      // in order to have styled graphs the css content used to render
      // graphs is retrieved & inject it into the svg as style tag
      var cssContentRequest = $http.get(chartCssUrl);
      cssContentRequest.success(function(cssContent) {

        // make sure we scale the padding and append it to the original styling
        // info: later declarations overwrite previous ones
        var style = originalStyle + '; background:#fff; ' + svgToPng.scalePaddingStyle(originalSvg, scalingFactor);

        // create svg element
        var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, style);

        // add styles and content to the svg
        var styles = '<style>' + cssContent + '</style>';
        svg.innerHTML = styles + originalSvg.html();

        // create img element with the svg as data source
        var svgXML = (new XMLSerializer()).serializeToString(svg);
        var tmpImage = document.createElement("img");
        tmpImage.width = orginalWidth * scalingFactor;
        tmpImage.height = orginalHeight * scalingFactor;
        tmpImage.src = "data:image/svg+xml;charset=utf-8,"+ svgXML;

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
            var data = canvas.toDataURL('image/jpeg', 1.0);
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
