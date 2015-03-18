/**
 *  A service with helper functions for optimization.
 */
define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('optimizationHelpers', function () {

    /*
     * Returns a new object with the parameters prepared for a server request.
     */
    var toRequestParameters = function(parameters, name) {
      console.log(parameters);
      return {
        name: name,
        objectives: angular.copy(parameters.objectives),
        constraints: angular.copy(parameters.constraints)
      };
    };

    /*
     * Convert server constraint parameters for usage in the controller scope.
     */
    var toScopeObjectives = function(responseObjectives) {
      console.log(responseObjectives);
      var objectives = angular.copy(responseObjectives);
      return objectives;
    };

    return {
      toRequestParameters: toRequestParameters,
      toScopeObjectives: toScopeObjectives
    };
 });
});
