define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
        $scope, $modalInstance, scenarios, scenario, parsets, progsets, ykeys) {

      $scope.scenario = scenario;
      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.editPar = {};
      var ykeys = ykeys.data.keys;

      $scope.scenarioExists = function () {
        return _.some(scenarios, function (scenario) {
          return $scope.scenario.name === scenario.name
            && $scope.scenario.id !== scenario.id;
        });
      }

      $scope.getParsInScenario = function () {
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

      $scope.getLongParName = function (short) {
        var pars = $scope.getParsInScenario();
        var par = _.findWhere(pars, { short: short });
        return par ? par.name : '';
      };

      $scope.getPopsOfPar = function (par) {
        if (ykeys.hasOwnProperty($scope.scenario.parset_id)) {
          var ykeysOfParset = ykeys[$scope.scenario.parset_id];
          if (ykeysOfParset.hasOwnProperty(par.name)) {
            return ykeysOfParset[par.name];
          }
        }
        return [];
      };

      $scope.selectNewPar = function () {
        $scope.editPar.for = $scope.getPopsOfPar($scope.editPar)[0].label;
      }

      var resetEditPar = function () {
        $scope.editPar = {}
        var pars = $scope.getParsInScenario();
        $scope.editPar.name = pars[0].short;
        $scope.selectNewPar();
      }

      $scope.addPar = function () {
        $scope.scenario.pars.push(angular.copy($scope.editPar));
        resetEditPar();
      }

      $scope.removePar = function (i) {
        $scope.scenario.pars = _.reject(
          $scope.scenario.pars, function (v, j) { return i = j });
      };

      $scope.isEditParValid = function () {
        function isNumber(n) {
          return !isNaN(parseFloat(n)) && isFinite(n);
        }
        var keys = ['startval', 'endval', 'startyear', 'endyear'];
        for (var i = 0; i < keys.length; i += 1) {
          if (!isNumber($scope.editPar[keys[i]])) {
            return false;
          }
        }
        return true;
      }

      $scope.save = function () {
        $modalInstance.close($scope.scenario);
      };

      if (!$scope.scenario.hasOwnProperty('name')) {
        $scope.scenario.active = true;
        $scope.scenario.id = null;
        $scope.scenario.progset_id = null;
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.pars = [];
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while ($scope.scenarioExists());
      }

      resetEditPar();

    });
});
