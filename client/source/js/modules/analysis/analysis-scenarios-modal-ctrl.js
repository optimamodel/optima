define(['./module'], function (module) {
  'use strict';

  module.controller('AnalysisScenariosModalController', function ($scope, $modalInstance, scenario, availableScenarioParams) {

    var initialize = function() {
      $scope.isNew = !scenario.name;

      // make sure the keys are the same objects as in the list for the select
      // to show the initial entries
      _(scenario.pars).each(function(entry) {
        // entry.keys = availableScenarioParams[0].keys;
        entry.keys = findScenarioParam(availableScenarioParams, entry.keys);
      });
      $scope.scenario = scenario;

      console.log(findScenarioParam(availableScenarioParams, $scope.scenario.keys));
      $scope.availableScenarioParams = availableScenarioParams;
    };

    var findScenarioParam = function(params, keys) {
      // TODO compare two arrays for equality
      return false;
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Your valiant attempts to fill in the form correctly have failed. Please try again');
      }

      $modalInstance.close($scope.scenario);
    };

    $scope.addParameter = function() {
      var entry = {keys:['condom','reg'], 'pop':0, 'startyear':2010,'endyear':2015,'startval':-1,'endval':1};
      scenario.pars.push(entry);
    };

    initialize();

  });

});
