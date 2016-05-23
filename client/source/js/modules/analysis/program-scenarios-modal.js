define(['angular'], function (module) {

	'use strict';

  return angular.module('app.program-scenarios-modal', [])
    .controller('ProgramScenariosModalController', function (
        $scope, $modalInstance, modalService, scenarios, scenario, parsets, progsets) {

      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.activePrograms = [];
      _.each(progsets[0].programs, function(program) {
        var years = program.ccopars.t;
        if (!_.isUndefined(years) && years.length > 0) {
          if (program.active) {
            $scope.activePrograms.push(program);
          }
        }
      });

      var nProgram = $scope.activePrograms.length;
      $scope.dataEntry = new Array(nProgram + 1);

      $scope.scenario = scenario;
      $scope.scenario_type = $scope
          .scenario.scenario_type.toLowerCase();

      $scope.scenarioExists = function() {
        var t = $scope.scenario;
        return _.some(scenarios, function (s) { return t.name === s.name && t.id !== s.id; });
      };

      var initNewScenario = function() {
        $scope.scenario[$scope.scenario_type] = [];
        _.each($scope.activePrograms, function (program) {
          $scope.scenario[$scope.scenario_type].push(
            {'program': program.short, 'values': []}
          );
        });
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.progset_id = $scope.progsets[0].id;
        $scope.scenario.active = true;
        $scope.scenario.years = [];
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while ($scope.scenarioExists());

        // $scope.table = {
        //   titles: _.pluck($scope.activePrograms, 'short');
        //   rows: [],
        //   types: [],
        //   widths: [],
        //   displayRowFns: [],
        //   options:
        //   validateFn:
        // }
      }

      $scope.getProgramsIndexRange = function() { return _.range(nProgram); };

      $scope.getYearIndexRange = function() { return _.range($scope.scenario.years.length); };

      $scope.getDataEntryRange = function() { return _.range($scope.dataEntry.length); };

      $scope.isDataInvalid = function() {
        // return _.some(_.map($scope.dataEntry, function(d) { return !_.isFinite(d) }));
        return false;
      };

      $scope.addDataEntryYear = function() {
        $scope.scenario.years.push($scope.dataEntry[0]);
        var changesByProgram = $scope.scenario[$scope.scenario_type];
        for (var iData=1; iData < $scope.dataEntry.length; iData+= 1) {
          var iProgram = iData - 1;
          changesByProgram[iProgram].values.push($scope.dataEntry[iData]);
        }
        _.each($scope.dataEntry, function(v, i, l) { l[i] = null; });
      };

      $scope.removeYear = function(i) {
        var changesByProgram = $scope.scenario[$scope.scenario_type];
        $scope.scenario.years.splice(i, 1);
        angular.forEach(changesByProgram, function (v, k) { v.values.splice(i, 1); });
      };

      $scope.save = function(){
        console.log('dialog scenario', $scope.scenario);
        $modalInstance.close($scope.scenario);
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      if (_.isUndefined($scope.scenario.parset_id)) {
        initNewScenario();
      }

    });
});
