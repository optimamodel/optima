define(['./module'], function (module) {
  'use strict';

  module.controller('AnalysisScenariosModalController', function ($scope,
    $modalInstance, scenario, availableScenarioParams, populationNames) {

    var initialize = function() {
      $scope.isNew = !scenario.name;

      // make sure the keys are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(scenario.pars).each(function(entry) {
        entry.keys = findScenarioParam(availableScenarioParams, entry.keys).keys;
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
     * Finds a scenario paramter based on the keys
     */
    var findScenarioParam = function(parameters, keys) {
      return _(parameters).find(function(parameterEntry) {
        return areEqualArrays(parameterEntry.keys, keys);
      });
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Your valiant attempts to fill in the form correctly have failed. Please try again');
      }

      $modalInstance.close($scope.scenario);
    };

    $scope.addParameter = function() {
      var entry = {keys: availableScenarioParams[0].keys, 'pop': 0, 'startyear':2010,'endyear':2015,'startval':-1,'endval':1};
      scenario.pars.push(entry);
    };

    initialize();

  });

});
