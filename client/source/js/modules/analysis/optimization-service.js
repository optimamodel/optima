/**
 *  A service with helper functions for optimization.
 */
define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('optimizationHelpers', function () {

    /*
     * Returns a new object with the parameters prepared for a server request.
     */
    var toRequestParameters = function(scopeParameters, name, timelimit) {
      var objectives = angular.copy(scopeParameters.objectives);

      objectives.money.objectives = _(objectives.money.objectives).mapObject(function(objective) {
        objective.by = objective.by / 100.0;
        return objective;
      });

      var parameters = {
        name: name,
        objectives: objectives,
        constraints: angular.copy(scopeParameters.constraints)
      };
      if (timelimit) {
        parameters.timelimit = timelimit;
      }
      return parameters;
    };

    /*
     * Convert server objective parameters for usage in the controller scope.
     */
    var toScopeObjectives = function(responseObjectives) {
      var objectives = angular.copy(responseObjectives);

      objectives.money.objectives = _(objectives.money.objectives).mapObject(function(objective) {
        objective.by = objective.by * 100;
        return objective;
      });

      return objectives;
    };

    return {
      toRequestParameters: toRequestParameters,
      toScopeObjectives: toScopeObjectives
    };
 });
});
