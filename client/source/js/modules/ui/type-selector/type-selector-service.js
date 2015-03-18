/**
 *  A service with helper functions for calibration.
 */
define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.factory('typeSelector', function (CONFIG) {

    /**
     * Iterate through all the types & disable the once where data is missing.
     */
    var enableAnnualCostOptions = function (types, graphData) {
      return _(types.financialAnnualCosts).each(function(entry) {
        if (graphData && graphData.costann &&
          graphData.costann.existing &&
          graphData.costann.existing[entry.id] &&
          graphData.costann.existing[entry.id].legend &&
          graphData.costann.existing[entry.id].legend.length) {
            entry.disabled = false;
          }
        });
    };

    var resetAnnualCostOptions = function(types) {
      return _(types.financialAnnualCosts).each(function(entry) {
        entry.disabled = true;
      });
    };

    return {
      enableAnnualCostOptions: enableAnnualCostOptions,
      resetAnnualCostOptions: resetAnnualCostOptions,
      types: angular.copy(CONFIG.GRAPH_TYPES)
    };
 });
});
