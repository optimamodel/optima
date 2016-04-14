define(['angular'], function (module) {

	'use strict';

  function range(n) {
    var result = [];
    for (var i = 0; i < n; i+=1) {
      result.push(i);
    }
    return result;
  }

  return angular.module('app.program-scenarios-modal', [])
    .controller('ProgramScenariosModalController', function (
        $scope, $modalInstance, modalService, scenarios, scenario, parsets,
        progsets) {

      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.activePrograms = _.filter(progsets[0].programs, {active: true});
      var nProgram = $scope.activePrograms.length;
      $scope.scenario = scenario;
      $scope.scenario_type = $scope.scenario.scenario_type.toLowerCase();
      if (!$scope.scenario[$scope.scenario_type]) {
        $scope.scenario[$scope.scenario_type] = [];
        _.forEach($scope.activePrograms, function (program) {
          $scope.scenario[$scope.scenario_type].push(
            {'program': program.short_name, 'values': []}
            );
        });
      }
      $scope.scenario.active = true;
      if(!$scope.scenario.years) {
        $scope.scenario.years = [];
      }
      $scope.dataEntry = new Array(nProgram + 1);
      $scope.timeChangesByProgram = $scope.scenario[$scope.scenario_type];

      $scope.getProgramsIndexRange = function() {
        return range(nProgram);
      };

      $scope.getYearIndexRange = function() {
        return range($scope.scenario.years.length);
      };

      $scope.getDataEntryRange = function() {
        return range($scope.dataEntry.length);
      };

      $scope.scenarioExists = function() {
        return _.some(scenarios, function (scenario) {
            return $scope.scenario.name === scenario.name && $scope.scenario.id !== scenario.id;
        });
      };

      // initialize scenario
      if (!$scope.hasOwnProperty("parset_id")) {
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.progset_id = $scope.progsets[0];
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while ($scope.scenarioExists());
      }

      $scope.save = function(){
        var scenario = {
          "scenario_type": $scope.scenario_type,
          "name": $scope.scenario.name,
          "parset_id": $scope.scenario.parset_id || null,
          "active": true,
          "years": $scope.scenario.years,
          "id": $scope.scenario.id || null,
          "progset_id": $scope.scenario.progset_id.id || null
        };
        scenario[$scope.scenario_type] = $scope.scenario[$scope.scenario_type];
        $modalInstance.close($scope.scenario);
      };

      $scope.isDataValid = function() {
        return true;
      };

      $scope.addDataEntryYear = function() {
        $scope.scenario.years.push($scope.dataEntry[0]);
        for (var i=1; i < $scope.dataEntry.length; i+= 1) {
          var iProgram = i - 1;
          var data = $scope.dataEntry[i]
          $scope.timeChangesByProgram[iProgram].values.push(data);
        }
        for (var i=0; i < $scope.dataEntry.length; i+= 1) {
          $scope.dataEntry[i] = null;
        }
      };

      $scope.removeYear = function(i) {
        $scope.yearEntries = _.reject($scope.yearEntries, function (param, j) { return j === i });
        if (angular.isDefined($scope.scenario.years[i])) {
          $scope.scenario.years.splice(i, 1);
        }
        if (angular.isDefined($scope.scenario[$scope.scenario_type]) && ($scope.scenario[$scope.scenario_type].length > 0)) {
          angular.forEach($scope.scenario[$scope.scenario_type], function (val, key) {
            val.values.splice(i, 1);
          });
        }
      };


    });
});
