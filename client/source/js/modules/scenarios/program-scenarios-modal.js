define(['angular', 'underscore'], function(angular, _) {

  'use strict';

  return angular.module('app.program-scenarios-modal', [])
      .controller('ProgramScenariosModalController', function(
          $scope, $modalInstance, modalService, scenarios, scenario,
          parsets, progsets, years, budgetsByProgsetId,
          coveragesByParsetIdyProgsetId) {

        function initialize() {
          $scope.parsets = parsets;
          $scope.progsets = progsets;
          $scope.years = years;

          console.log('budgetsByProgsetId', budgetsByProgsetId);

          $scope.state = {};

          $scope.otherNames = _.without(_.pluck(scenarios, 'name'), scenario.name);
          $scope.scenario = scenario;
          $scope.scenario_type = $scope.scenario.scenario_type;
          $scope.scenario_type = $scope.scenario_type.toLowerCase();

          if (_.isUndefined($scope.scenario.parset_id)) {
            initNewScenario();
          }
          $scope.resetParsetAndProgset();

        }

        $scope.resetParsetAndProgset = function() {
          $scope.state.progset = _.findWhere(progsets, {id: scenario.progset_id});
          $scope.state.parset = _.findWhere(parsets, {id: scenario.parset_id});

          $scope.state.programs = [];
          _.each($scope.state.progset.programs, function(program) {
            if (program.active) {
              $scope.state.programs.push(program);
            }
          });
          console.log('state.programs', $scope.state.programs);

          extractYearEntries();
        };

        $scope.getScenarioType = function() {
          var s = $scope.scenario_type;
          return s.charAt(0).toUpperCase() + s.slice(1);
        };

        $scope.isNameClash = function(scenario_name) {
          return _.contains($scope.otherNames, scenario_name);
        };

        function initNewScenario() {
          $scope.scenario[$scope.scenario_type] = [];
          $scope.scenario.parset_id = $scope.parsets[0].id;
          $scope.scenario.progset_id = $scope.progsets[0].id;
          $scope.scenario.active = true;
          var i = 1;
          do {
            $scope.scenario.name = "Scenario " + i;
            i += 1;
          } while ($scope.isNameClash($scope.scenario.name));
        }

        $scope.addYearEntry = function() {
          $scope.state.yearEntries.push({
            value: new Date().getFullYear(),
            programs: []
          });
        };

        $scope.addProgram = function(yearEntry) {
          var newProgram = {
            short: $scope.state.programs[0].short,
            value: null
          };
          $scope.selectProgram(yearEntry, newProgram);
          yearEntry.programs.push(newProgram);
        };

        $scope.addAllPrograms = function(yearEntry) {
        console.log('$scope.state.programs', $scope.state.programs)
          for (newProg in $scope.state.programs) {
            var newProgram = {
              short: newProg.short,
              value: null
            };
            console.log('newProg', newProg, 'yearEntry', yearEntry)
            $scope.selectProgram(yearEntry, newProgram);
            yearEntry.programs.push(newProgram);
            console.log('programs', yearEntry.programs)
          }
        };

        $scope.selectProgram = function(yearEntry, program) {
          if ($scope.scenario_type == "budget") {
            var budgets = budgetsByProgsetId[$scope.scenario.progset_id];
            var value = budgets[program.short];
          } else if ($scope.scenario_type == "coverage") {
            var coveragesByProgsetId = coveragesByParsetIdyProgsetId[$scope.scenario.parset_id];
            var coveragesByYear = coveragesByProgsetId[$scope.scenario.progset_id];
            console.log('coveragesByYear', coveragesByYear);
            console.log('program', program);
            var value = coveragesByYear[yearEntry.value][program.short];
          }
          program.value = value;
        };

        $scope.removeProgram = function(yearEntry, iProgram) {
          yearEntry.programs.splice(iProgram, 1);
        };

        $scope.removeYearEntry = function(i) {
          $scope.state.yearEntries.splice(i, 1);
        };

        function extractYearEntries() {
          $scope.state.yearEntries = _.map(
            $scope.scenario.years,
            function(year) { return {value: year, programs: []}; });

          _.each(
            $scope.scenario[$scope.scenario_type],
            function(program) {
              _.each(program.values, function(value, i) {
                $scope.state.yearEntries[i].programs.push({
                  'short': program.program,
                  'value': value
                })
              });
            });

          console.log('extracted year entries', $scope.state.yearEntries);
        }

        function revertYearEntriesToScenario() {
          $scope.scenario.years = _.pluck($scope.state.yearEntries, 'value');

          var programShorts = _.uniq(_.flatten(_.map(
            $scope.state.yearEntries,
            function(year) {
              return _.pluck(year.programs, 'short');
            }
          )));

          var iProgramByShort = {};
          _.each(programShorts, function(short, i) {
            iProgramByShort[short] = i;
          });

          var nYear = $scope.state.yearEntries.length;
          $scope.scenario[$scope.scenario_type] = _.map(
            programShorts,
            function(short) { return {program: short, values: new Array(nYear)}; }
          );
          var programList = $scope.scenario[$scope.scenario_type];

          _.each($scope.state.yearEntries, function(year, iYear) {
            _.each(year.programs, function(program) {
              var iProgram = iProgramByShort[program.short];
              programList[iProgram].values[iYear] = program.value;
            });
          });
          console.log('output scenario', $scope.scenario);
        }

        $scope.save = function() {
          revertYearEntriesToScenario();
          console.log('saving scenario', $scope.scenario);
          $modalInstance.close($scope.scenario);
        };

        $scope.cancel = function() {
          $modalInstance.dismiss("cancel");
        };

        initialize();
      });
});
