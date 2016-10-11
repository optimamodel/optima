define(['angular', 'underscore'], function(module, _) {

  'use strict';

  return angular.module('app.program-scenarios-modal', [])
      .controller('ProgramScenariosModalController', function(
          $scope, $modalInstance, modalService, scenarios, scenario,
          parsets, progsets, years, budgetsByProgsetId) {

        function initialize() {
          $scope.parsets = parsets;
          $scope.progsets = progsets;

          $scope.activePrograms = [];
          _.each(progsets[0].programs, function(program) {
            if (program.active) {
              $scope.activePrograms.push(program);
            }
          });
          $scope.nProgram = $scope.activePrograms.length;

          $scope.dataEntry = new Array($scope.nProgram + 1);

          $scope.scenario = scenario;
          $scope.scenario_type = $scope.scenario.scenario_type;
          $scope.scenario_type = $scope.scenario_type.toLowerCase();
          if (_.isUndefined($scope.scenario.parset_id)) {
            initNewScenario();
          }

          convertYears();
          revertYears();
          console.log('activePrograms', $scope.activePrograms);
          console.log('converted scenario', $scope.scenario);
          console.log('budgetsByProgsetId', budgetsByProgsetId);
        }

        $scope.getActivePrograms = function() {
          return $scope.activePrograms;
        };

        $scope.checkForClashingName = function(scenario) {
          function hasClash(s) {
            return s.name == scenario.name && s.id != scenario.id;
          }
          return _.some(scenarios, hasClash);
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
          } while ($scope.checkForClashingName($scope.scenario));

        }

        $scope.addYear = function() {
          $scope.years.push({
            value: new Date().getFullYear(),
            programs: []
          });
        };

        $scope.addProgram = function(year) {
          var newProgram = {
            short: $scope.getActivePrograms()[0].short,
            value: null
          };
          $scope.changeProgram(newProgram);
          year.programs.push(newProgram);
        };

        $scope.changeProgram = function(program) {
          if ($scope.scenario_type == "budget") {
            var defaultBudget = budgetsByProgsetId[$scope.scenario.progset_id];
            var value = defaultBudget[program.short];
          }
          program.value = value;
        };

        $scope.removeProgram = function(years, iProgram) {
          years.programs.splice(iProgram, 1);
        };

        $scope.getSelectableYears = function(year) {
          return years;
        };

        $scope.getScenarioType = function() {
          var s = $scope.scenario_type;
          return s.charAt(0).toUpperCase() + s.slice(1);
        };

        $scope.removeYear = function(i) {
          console.log('delete iyear', i);
          var changesByProgram = $scope.scenario[$scope.scenario_type];
          $scope.years.splice(i, 1);
        };

        function convertYears() {
          console.log('original scenario', $scope.scenario);
          $scope.years = _.map(
            $scope.scenario.years,
            function(year) { return {value: year, programs: []}; });

          _.each(
            $scope.scenario[$scope.scenario_type],
            function(program) {
              _.each(program.values, function(value, i) {
                $scope.years[i].programs.push({
                  'short': program.program,
                  'value': value
                })
              });
            });

          console.log('input years', $scope.years);
        }

        function revertYears() {
          console.log('input years', $scope.years);
          $scope.scenario.years = _.pluck($scope.years, 'value');

          var programShorts = _.uniq(_.flatten(_.map(
            $scope.years,
            function(year) {
              return _.pluck(year.programs, 'short');
            }
          )));

          console.log(programShorts);
          var iProgramByShort = {};
          _.each(programShorts, function(short, i) {
            iProgramByShort[short] = i;
          });

          var nYear = $scope.years.length;
          $scope.scenario[$scope.scenario_type] = _.map(
            programShorts,
            function(short) { return {program: short, values: new Array(nYear)}; }
          );
          var programList = $scope.scenario[$scope.scenario_type];

          _.each($scope.years, function(year, iYear) {
            _.each(year.programs, function(program) {
              var iProgram = iProgramByShort[program.short];
              programList[iProgram].values[iYear] = program.value;
            });
          });
          console.log('output scenario', $scope.scenario);
        }

        $scope.save = function() {
          revertYears();
          console.log('saving scenario', $scope.scenario);
          $modalInstance.close($scope.scenario);
        };

        $scope.cancel = function() {
          $modalInstance.dismiss("cancel");
        };

        initialize();
      });
});
