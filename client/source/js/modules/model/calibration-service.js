/**
 *  A service with helper functions for calibration.
 */
define([
  './module',
], function (module) {
  'use strict';

  module.factory('calibration', [ function () {

    /*
     * Returns a new f parameter object with string values parsed to decimal numbers.
     */
    var prepareF = function (original_f) {
      var f = angular.copy(original_f);

      f.dx = _(f.dx).map(parseFloat);
      f.force = _(f.force).map(parseFloat);
      f.init = _(f.init).map(parseFloat);
      f.popsize = _(f.popsize).map(parseFloat);
      return f;
    };

    /*
     * Returns a new m parameter object with string values parsed to decimal numbers.
     */
    var prepareM = function(original_m) {
      var m = angular.copy(original_m);

      _(m).each(function (parameter) {
        parameter.data = parseFloat(parameter.data);
      });
      return m;
    };

    /*
     * Convert the form parameters to provide it for the server.
     */
    var toRequestParameters = function(parameters) {
      return parameters;
    };

    /*
     * Convert server parameters for usage in the controller scope.
     */
    var toScopeParameters = function(parameters, meta, shouldTranformF) {

      var transformedF = shouldTranformF ? {} : prepareF(parameters.F[0]);

      return {
        types: {
          force: 'Relative force-of-infection for ',
          popsize: 'Initial population size for ',
          init: 'Initial prevalence for ',
          dx: [
            'Overall population initial relative testing rate',
            'Overall population final relative testing rate',
            'Year of mid change in overall population testing rate',
            'Testing rate slope parameter'
          ]
        },
        meta: meta,
        f: transformedF,
        m: parameters.M,
        cache: {
          f: angular.copy(transformedF),
          m: angular.copy(parameters.M),
          response: null
        }
      };
    };

    return {
      toRequestParameters: toRequestParameters,
      toScopeParameters: toScopeParameters,
      prepareM: prepareM,
      prepareF: prepareF
    };
 }]);
});
