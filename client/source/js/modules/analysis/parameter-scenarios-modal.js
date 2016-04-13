define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
      $scope, $modalInstance, modalService, scenarios, scenario, parsets, progsets, ykeys) {

      $scope.scenario = scenario;
      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.editPar = {};

      var ykeys = ykeys.data.keys;

      $scope.scenarioExists = function() {
        return _.some(scenarios, function (scenario) {
          return $scope.scenario.name === scenario.name
              && $scope.scenario.id !== scenario.id;
        });
      }

      $scope.getParsInScenario = function() {
        var parsets = $scope.parsets;
        var parset_id = $scope.scenario.parset_id;
        if (parset_id) {
          parsets = _.filter($scope.parsets, {id: parset_id});
        };
        if (parsets.length > 0) {
          return _.filter(parsets[0].pars[0], {visible: 1});
        }
        return [];
      };

      $scope.getPopsOfPar = function(par) {
        if (ykeys.hasOwnProperty($scope.scenario.parset_id)) {
          var ykeysOfParset = ykeys[$scope.scenario.parset_id];
          if (ykeysOfParset.hasOwnProperty(par.name)) {
            return ykeysOfParset[par.name];
          }
        }
        return [];
      };

      $scope.selectNewPar = function() {
        $scope.editPar.for = $scope.getPopsOfPar($scope.editPar)[0].label;
      }

      $scope.clearEditPar = function (){
        $scope.editPar = {}
        var pars = $scope.getParsInScenario();
        $scope.editPar.name = pars[0].short;
        $scope.selectNewPar();
      }

      $scope.addPar = function() {
        $scope.scenario.pars.push(angular.copy($scope.editPar));
        $scope.clearEditPar();
      }

      $scope.removePar = function(i) {
        $scope.scenario.pars = _.reject($scope.scenario.pars, function (val, j) { return i = j });
      };

      function isNumber(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
      }

      $scope.isEditParValid = function() {
        var keys = ['startval', 'endval', 'startyear', 'endyear'];
        for (var i=0; i<keys.length; i+=1) {
          if (!isNumber($scope.editPar[keys[i]])) {
            return false;
          }
        }
        return true;
      }

      $scope.save = function() {
        var scenario = {
          "scenario_type": $scope.scenario.scenario_type,
          "name": $scope.scenario.name,
          "parset_id": $scope.scenario.parset_id || null,
          "active": true,
          "pars": $scope.scenario.pars,
          "id": $scope.scenario.id || null,
          "progset_id": $scope.scenario.progset_id || null
        };
        $modalInstance.close(scenario);
      };

      $scope.scenario.parset_id = $scope.parsets[0].id;
      $scope.scenario.pars = [];
      var i = 1;
      while (!$scope.scenario.hasOwnProperty('name') || $scope.scenarioExists()) {
        $scope.scenario.name = "Scenario " + i;
        i += 1;
      };

      $scope.clearEditPar();


    });
});
