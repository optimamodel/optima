define(['d3'], function (d3) {
  'use strict';

  // Orginally taken from d3: d3_format_precision
  var formatPrecision = function (x, p) {
    return p - (x ? Math.ceil(Math.log(x) / Math.LN10) : 1);
  };

  // Orginally taken from d3: d3.round
  var round = function (x, n) {
    return n ? Math.round(x * (n = Math.pow(10, n))) / n : Math.round(x);
  };

  // Orginally taken from d3: d3.formatPrefix
  var formatPrefix = function(d, i) {
    var k = Math.pow(10, Math.abs(8 - i) * 3);
    return {
      scale: i > 8 ? function(d) {
        return d / k;
      } : function(d) {
        return d * k;
      },
      symbol: d
    };
  };

  /**
   * Returns the provided number rounded up.
   *
   * For numbers larger then 1 it simply rounds up to the next integer.
   * For numbers smaller than 1 it rounds up to the first non zero decimal.
   *
   * Example:
   * 2.4 -> 3
   * 0.00242 -> 0.003
   * 0.041 -> 0.05
   * 0 -> 0
   */
  var flexCeil = function(value) {
    if (value === 0) return 0;
    if (value >= 1.0) return Math.ceil(value);
    var multi=1.0;
    while (value < 1.0){
      multi /= 10;
      value *= 10;
    }
    return Math.ceil(value)*multi;
  };


  // Orginally taken from d3 and modified to use the requested abbreviations.
  var formatPrefixes = [ "y", "z", "a", "f", "p", "n", "µ", "milli", "", "K",
    "m", "bn", "T", "P", "E", "Z", "Y" ].map(formatPrefix);

  // Orginally taken from d3: d3_formatPrefix
  var customFormatPrefix = function(value, precision) {
    var i = 0;
    if (value) {
      if (value < 0) value *= -1;
      if (precision) value = round(value, formatPrecision(value, precision));
      i = 1 + Math.floor(1e-12 + Math.log(value) / Math.LN10);
      i = Math.max(-24, Math.min(24, Math.floor((i - 1) / 3) * 3));
    }
    return formatPrefixes[8 + i / 3];
  };

  /**
   * Returns the formated value which includes a numeric value & prefix.
   */
  var customFormat = function(value) {
    var formattedValue = customFormatPrefix(Math.abs(value));
    return formattedValue.scale(value) + formattedValue.symbol;
  };

  /**
   * Returns an appropriate tick format depending on the range of the values.
   *
   * For a range smaller than 0.01 a precesion of 3 decimal points is chosen.
   * For a range smaller than 1 a precesion of 2 decimal points is chosen.
   * For a range smaller than 10 a precesion of 1 decimal points is chosen.
   * For a range between 10 & 10,000 a precesion of 0 decimal points is chosen.
   * For a range between 10,000 & 100,000 a precesion of 0 decimal points is
   * chosen with a comma as thousands separator.
   * For a range larger than 100,000 the numbers are custom suffixed.
   */
  var evaluateTickFormat = function(min, max) {
    var range = Math.abs(max) - Math.abs(min);
    if (range < 0.01) {
      return '.3f';
    } else if (range < 1) {
      return '.2f';
    } else if (range < 10) {
      return '.1f';
    } else if (range < 10000) {
      return '.0f';
    } else if (range > 100000) {
      return 'custom';
    } else {
      return ',.0f';
    }
  };

  /**
   * Returns a formated value based on the provided format.
   *
   * The format should be determined by using evaluateTickFormat, but can be any
   * specified by d3. In addition the format value 'custom' can be used for the
   * customized formatting using K for 10e3, m for 10e6 and bn for 10e9.
   */
  var customTickFormat = function (value, format) {
    if (format == 'custom') {
      return customFormat(value);
    } else {
      return d3.format(format)(value);
    }
  };

  return {
    evaluateTickFormat: evaluateTickFormat,
    customTickFormat: customTickFormat,
    flexCeil: flexCeil
  };
});
