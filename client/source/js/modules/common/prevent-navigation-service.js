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
  .factory('PreventNavigation', [ '$state', 'modalService', function ($state, modalService) {
    
    /**
     * PreventNavigation class constructor
     */
    function PreventNavigation () {
    };


    /**
     * Displays a modal confirmation window with the given message and action.
     * Evaluates callback when the user confirms going to the target state.
     */
    PreventNavigation.prototype.confirmPopup = function (message, head, onAccept, onReject) {
      modalService.confirm(
        onAccept,
        onReject,
        'Yes',
        'No',
        message,
        head
      );
    };

    /**
     * Displays a modal confirmation window asking the user for confirmation 
     * about navigating out of the current state.
     */
    PreventNavigation.prototype.confirmNavigation = function (event, toState) {
      event.preventDefault();
      var message = 'Are you sure you want to leave this page?';
      var head = 'You have changed values';
      this.confirmPopup(message, head, function () {
        console.log('going to state: ',toState.name);
        $state.go(toState.name);
      });      
    };

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
      if( !this.canNavigate() ){
        this.confirmNavigation(event, toState);
      }
    };

    return new PreventNavigation();
 }]);
});
