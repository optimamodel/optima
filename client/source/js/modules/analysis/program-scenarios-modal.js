define(['angular'], function (module) {

	'use strict';

  return angular.module('app.program-scenarios-modal', [])
    .controller('ProgramScenariosModalController', function (
        $scope, $modalInstance, modalService, scenarios, scenario, parsets, progsets) {

      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.activePrograms = _.filter(progsets[0].programs, {active: true});

      var nProgram = $scope.activePrograms.length;
      $scope.dataEntry = new Array(nProgram + 1);

      $scope.scenario = scenario;
      $scope.scenario_type = $scope.scenario.scenario_type.toLowerCase();

      $scope.scenarioExists = function() {
        var t = $scope.scenario;
        return _.some(scenarios, function (s) { return t.name === s.name && t.id !== s.id; });
      };

      var initNewScenario = function() {
        $scope.scenario[$scope.scenario_type] = [];
        _.each($scope.activePrograms, function (program) {
          $scope.scenario[$scope.scenario_type].push(
            {'program': program.short_name, 'values': []}
          );
        });
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.progset_id = $scope.progsets[0].id;
        $scope.scenario.years = [];
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while ($scope.scenarioExists());
      }

      $scope.getProgramsIndexRange = function() { return _.range(nProgram); };

      $scope.getYearIndexRange = function() { return _.range($scope.scenario.years.length); };

      $scope.getDataEntryRange = function() { return _.range($scope.dataEntry.length); };

      $scope.save = function(){ $modalInstance.close($scope.scenario); };

      $scope.isDataInvalid = function() {
        return _.some(_.map($scope.dataEntry, function(d) { return !_.isFinite(d) }));
      };

      $scope.addDataEntryYear = function() {
        $scope.scenario.years.push($scope.dataEntry[0]);
        var changesByProgram = $scope.scenario[$scope.scenario_type];
        for (var iData=1; iData < $scope.dataEntry.length; iData+= 1) {
          var iProgram = iData - 1;
          changesByProgram[iProgram].values.push($scope.dataEntry[iData]);
        }
        for (var i=0; i < $scope.dataEntry.length; i+= 1) {
          $scope.dataEntry[i] = null;
        }
      };

      $scope.removeYear = function(i) {
        var changesByProgram = $scope.scenario[$scope.scenario_type];
        $scope.scenario.years.splice(i, 1);
        angular.forEach(changesByProgram, function (v, k) { v.values.splice(i, 1); });
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      if (_.isUndefined($scope.scenario.parset_id)) {
        initNewScenario();
      }

    });
});
