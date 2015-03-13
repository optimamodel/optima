/**
 *  A service with helper functions for calibration.
 */
define([
  './module',
], function (module) {
  'use strict';

  module.factory('calibration', [ function () {

    var lastSavedCalibrationResponse;
    var lastPreviewCalibrationResponse;

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
     * Returns a new object with the form parameters prepared for a server request.
     */
    var toRequestParameters = function(scopeParameters, doSave) {
      var parameters = {
        F: prepareF(scopeParameters.f),
        M: prepareM(scopeParameters.m)
      };
      if (doSave) {
        parameters.doSave = true;
      }
      return parameters;
    };

    /*
     * Convert server parameters for usage in the controller scope.
     */
    var toScopeParameters = function(parameters, meta, shouldTranformF) {

      var fParameters = parameters.F[0] ? prepareF(parameters.F[0]) : {};

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
        f: fParameters,
        m: parameters.M
      };
    };

    var storeLastSavedResponse = function (calibrationResponse) {
      lastSavedCalibrationResponse = calibrationResponse;
    };

    var storeLastPreviewResponse = function (calibrationResponse) {
      lastPreviewCalibrationResponse = calibrationResponse;
    };

    var lastSavedResponse = function () {
      return angular.copy(lastSavedCalibrationResponse);
    };

    var lastPreviewResponse = function () {
      return angular.copy(lastPreviewCalibrationResponse);
    };

    return {
      toRequestParameters: toRequestParameters,
      toScopeParameters: toScopeParameters,
      storeLastSavedResponse: storeLastSavedResponse,
      storeLastPreviewResponse: storeLastPreviewResponse,
      lastSavedResponse: lastSavedResponse,
      lastPreviewResponse: lastPreviewResponse
    };
 }]);
});
