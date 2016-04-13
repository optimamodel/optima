define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
      $scope, $modalInstance, modalService, scenarios, scenario, parsets, progsets, ykeys) {

      $scope.row = scenario;
      $scope.scenario = scenario;
      $scope.parsets = parsets;
      $scope.progsets = progsets;

      var ykeys = ykeys.data.keys;

      clearEditPar();

      $scope.parsForSelectedParset = function() {
        var parset = _.filter($scope.parsets, {id: scenario.parset_id});
        if (parset.length > 0) {
          return _.filter(parset[0].pars[0], {visible: 1});
        }
        return [];
      };

      $scope.popsForParam = function(param) {
        if (ykeys.hasOwnProperty(scenario.parset_id)) {
          var ykeysOfParset = ykeys[scenario.parset_id];
          if (ykeysOfParset.hasOwnProperty(param)) {
            return ykeysOfParset[param];
          }
        }
        return [];
      };

      function clearEditPar() {
        $scope.editPar = {};
      }

      $scope.addPar = function() {
        scenario.pars.push(angular.copy($scope.editPar));
      }

      $scope.manageScenario = function(){
        var scenario = {
          "scenario_type": $scope.row.scenario_type,
          "name": $scope.row.name,
          "parset_id": $scope.row.parset_id || null,
          "active": true,
          "pars": $scope.row.pars,
          "id": $scope.row.id || null,
          "progset_id": $scope.row.progset_id || null
        };

        $modalInstance.close(scenario);
      };

      $scope.addParam = function(scenario) {
        if (!scenario.pars) {
          scenario.pars = [];
        }
        scenario.pars.push({});
      };

      $scope.removeParam = function(scenario, paramIndex) {
        scenario.pars = _.reject(scenario.pars, function (param, index) {
          return index === paramIndex
        });
      };

      $scope.closeModal = function() {
        $modalInstance.close($scope.row);
      };

      $scope.scenarioExists = function() {
        return _.some(scenarios, function (scenario) {
          return $scope.row.name === scenario.name && $scope.row.id !== scenario.id;
        });
      }

    });
});
