/**
 * AnalysisScenariosModalController is the scenario editor.
 * It sets title and adds and removes parameters of the model (scenario to be analized).
 */
define(['./module'], function (module) {
  'use strict';

  module.controller('AnalysisScenariosModalController', function ($scope,
    $modalInstance, scenario, availableScenarioParams, populationNames) {

    var initialize = function() {
      $scope.isNew = !scenario.name;

      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(scenario.pars).each(function(entry) {
        entry.names = findScenarioParam(availableScenarioParams, entry.names).names;
      });

      $scope.scenario = scenario;
      $scope.availableScenarioParams = availableScenarioParams;
      $scope.populationNames = populationNames;
    };

    /*
     * Returns true of the two provided arrays are identic
     */
    var areEqualArrays = function(arrayOne, arrayTwo) {
      return _(arrayOne).every(function(element, index) {
        return element === arrayTwo[index];
      });
    };

    /*
     * Finds a scenario paramter based on the names
     */
    var findScenarioParam = function(parameters, names) {
      return _(parameters).find(function(parameterEntry) {
        return areEqualArrays(parameterEntry.names, names);
      });
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Your valiant attempts to fill in the form correctly have failed. Please try again');
      }

      $modalInstance.close($scope.scenario);
    };

    /**
     * Removes the parameter at the given index (without asking for confirmation).
     */
    $scope.removeParameter = function ($index) {
      scenario.pars.splice($index,1);
    };

    $scope.addParameter = function() {
      var entry = {
        names: availableScenarioParams[0].names, pops: 0,
        startyear: 2010, endyear: 2015, startval: -1, endval: 1
      };
      scenario.pars = scenario.pars || [];
      scenario.pars.push(entry);
    };

    initialize();

  });

});
