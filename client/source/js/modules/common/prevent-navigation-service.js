/**
 * A service to check whether prevent navigation on a state or not
 * initially results will be false, at time of start any process, for example Optimization
 * When start optimization set PreventNavigation.optimization to true and when navigating away 
 * from the screen show warning message
 */

define([
  'angular'
  ], function (angular) {
  'use strict';

  return angular.module('app.common.prevent-navigation',[])
  .factory('PreventNavigation', [ function () {
    
    /**
     * PreventNavigation class constructor
     */
    function PreventNavigation () {
    }

    /**
     * Answers true if the user can navigate out of the current state, false otherwise.
     */
    PreventNavigation.prototype.canNavigate = function () {
      return false;
    };

    /**
     * Reacts to the change of state attempt.
     */
    PreventNavigation.prototype.onStateChangeStart = function (event, toState, toParams, fromState, fromParams) {
      if(this.canNavigate()){
        console.info('going to state: ', toState);
      } else {
        console.warn('NOT going to state: ', toState);
      }
    };
    
    return new PreventNavigation();
 }]);
});
