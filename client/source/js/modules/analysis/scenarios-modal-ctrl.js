/**
 * AnalysisScenariosModalController is the scenario editor.
 * It sets title and adds and removes parameters of the model (scenario to be analized).
 */
define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('AnalysisScenariosModalController', function ($scope,
    $modalInstance, scenario, availableScenarioParameters, populationNames, modalService) {

    var initialize = function() {
      $scope.scenario = angular.copy(scenario);
      $scope.isNew = !$scope.scenario.name;
      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _($scope.scenario.pars).each(function(entry) {
        entry.names = findScenarioParameters(availableScenarioParameters, entry.names).names;
      });

      $scope.availableScenarioParameters = availableScenarioParameters;
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
    var findScenarioParameters = function(parameters, names) {
      return _(parameters).find(function(parameterEntry) {
        return areEqualArrays(parameterEntry.names, names);
      });
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined,'Your valiant attempts to fill in the form correctly have failed. Please try again');
      } else {
        $modalInstance.close($scope.scenario);
      }
    };

    /**
     * Removes the parameter at the given index (without asking for confirmation).
     */
    $scope.removeParameter = function ($index) {
      $scope.scenario.pars.splice($index,1);
    };

    /**
     * Add a new parameter to the currently open scenario.
     */
    $scope.addParameter = function() {
      var entry = {
        names: availableScenarioParameters[0].names, pops: 0,
        startyear: 2005, endyear: 2015,
        startval: angular.copy(availableScenarioParameters[0].values[0]),
        endval: angular.copy(availableScenarioParameters[0].values[0])
      };
      $scope.scenario.pars = $scope.scenario.pars || [];
      $scope.scenario.pars.push(entry);
    };

    /**
     * Update the start & end value to the default settings.
     *
     * This is useful when switching between parameters entries.
     */
    $scope.resetStartAndEndValue = function(parametersEntry) {
      var defaultParameters = findScenarioParameters(availableScenarioParameters, parametersEntry.names);
      parametersEntry.startval = angular.copy(defaultParameters.values[0]);
      parametersEntry.endval = angular.copy(defaultParameters.values[1]);
    };

    initialize();
  });

});
