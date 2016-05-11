/**
 *  A service with helper functions for optimization.
 */
define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('costCoverageHelpers', function () {

    var convertFromPercent = function (value) {
      if (typeof value !== "number" || isNaN(value)) {
        return NaN;
      }
      return value / 100;
    };

    var toRequestCoParams = function (coParams) {
      return _(coParams).map(function (effect) {
        return [
          convertFromPercent(effect[0]),
          convertFromPercent(effect[1]),
          convertFromPercent(effect[2]),
          convertFromPercent(effect[3])
        ];
      });
    };

    var setUpCoParamsFromEffects = function (effectNames) {
      var coParams = _(effectNames).map(function (effect) {
        if (effect.coparams) {
          return [
            (effect.coparams && effect.coparams[0]) ? effect.coparams[0] * 100 : null,
            (effect.coparams && effect.coparams[1]) ? effect.coparams[1] * 100 : null,
            (effect.coparams && effect.coparams[2]) ? effect.coparams[2] * 100 : null,
            (effect.coparams && effect.coparams[3]) ? effect.coparams[3] * 100 : null
          ];
        } else {
          return [null, null, null, null];
        }
      });
      return coParams;
    };

    return {
      setUpCoParamsFromEffects: setUpCoParamsFromEffects,
      toRequestCoParams: toRequestCoParams,
      convertFromPercent: convertFromPercent
    };
 });
});
