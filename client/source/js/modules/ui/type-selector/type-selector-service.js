define(['./module', 'angular'], function (module, angular) {
  'use strict';

  /**
   * Stores the chart types and provides helper functions for annual cost options.
   *
   * The types indicate which charts in a controller should be displayed as they
   * reflect the current selection made in the type-selector UI.
   */
  module.factory('typeSelector', function (CONFIG) {

    /**
     * Iterate through all the types & enable the once where data is missing.
     *
     * By default all options are disabled. This function enables some of these
     * options depending on the available chart data.
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

    /**
     * Disables all annual costs.
     *
     * Should be used in situations where new data is coming from a long a long
     * running process that might have different annual costs.
     */
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
