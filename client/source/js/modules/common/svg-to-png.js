define(['jquery', 'underscore'], function (jQuery, _) {
  'use strict';

  /**
   * Create SVG element
   *
   * With the scalingFactor argument a SVG image can be blown up.
   */
  var createSvg = function(viewBoxWidth, viewBoxheight, scalingFactor, originalStyle, id) {
    var xmlns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(xmlns, "svg");
    var viewBox = "0 0 " + viewBoxWidth + " " + viewBoxheight;
    svg.setAttributeNS(null, "viewBox", viewBox);
    svg.setAttributeNS(null, "width", viewBoxWidth * scalingFactor);
    svg.setAttributeNS(null, "height", viewBoxheight * scalingFactor);
    svg.setAttributeNS(null, "version", "1.1");
    svg.setAttributeNS(null, "style", originalStyle);
    if (id) {
      svg.setAttributeNS(null, "id", id);
    }
    return svg;
  };

  /**
   * Parse the number from a pixel string value.
   *
   * To avoid having NaN in CSS it returns 0 in case the value can't be parsed.
   */
  var parsePixel = function (value) {
    var parsedValue = parseFloat(value);
    return isNaN(parsedValue) ? 0 : parsedValue;
  };

  /**
   * Returns the string content for the scaled padding values.
   *
   * This utility function can be used when scaling an SVG image to preserve
   * a proper padding.
   */
  var scalePaddingStyle = function (svgElement, scalingFactor) {
    var attributes = [
      'padding-top',
      'padding-right',
      'padding-bottom',
      'padding-left'
    ];

    var $svg = jQuery(svgElement);
    var scaledAttributes = _(attributes).map(function(attributeName) {
      var value = parsePixel($svg.css(attributeName)) * scalingFactor;
      return attributeName + ": " + value + "px";
    });

    return scaledAttributes.join('; ');
  };

  return {
    parsePixel: parsePixel,
    scalePaddingStyle: scalePaddingStyle,
    createSvg: createSvg
  };
});
