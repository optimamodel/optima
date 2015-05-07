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
  .factory('PreventNavigation', [function () {
    
    /**
     * PreventNavigation class constructor
     */
    function PreventNavigation() {
      this.calibration = false;
      this.costcoverage = false;
      this.optimization = false;
      this.scenario = false;
    }

    /**
     * set value for calibration
     *
     * @param bool
     * @return 
     */
    PreventNavigation.prototype.setCalibration = function(bool) {
      this.calibration = bool;
    }

    /**
     * get value of calibration
     *
     * @param
     * @return bool
     */
    PreventNavigation.prototype.getCalibration = function() {
      return this.calibration;
    }

    /**
     * set value for costcoverage
     *
     * @param bool
     * @return 
     */
    PreventNavigation.prototype.setCostcoverage = function(bool) {
      this.costcoverage = bool;
    }

    /**
     * get value of costcoverage
     *
     * @param bool
     * @return 
     */
    PreventNavigation.prototype.getCostcoverage = function() {
      return this.costcoverage;
    }

    /**
     * set value for optimization
     *
     * @param bool
     * @return 
     */
    PreventNavigation.prototype.setOptimization = function(bool) {
      this.optimization = bool;
    }

    /**
     * get value of optimization
     *
     * @param
     * @return bool
     */
    PreventNavigation.prototype.getOptimization = function() {
      return this.optimization;
    }

    /**
     * set value for scenario
     *
     * @param bool
     * @return 
     */
    PreventNavigation.prototype.setScenario = function(bool) {
      this.scenario = bool;
    }

    /**
     * get value of scenario
     *
     * @param
     * @return bool
     */
    PreventNavigation.prototype.getScenario = function() {
      return this.scenario;
    }
    
    return new PreventNavigation();
 }]);
});
