define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
        $scope, $modalInstance, scenarios, scenario, parsets,
        progsets, ykeys, years) {

      $scope.scenario = scenario;
      $scope.parsets = parsets;
      $scope.progsets = progsets;
      $scope.editPar = {};
      var editKeys = ['startval', 'endval', 'startyear', 'endyear'];

      function initialize() {
        if (_.isUndefined($scope.scenario.name)) {
          initNewScenario();
        }
        resetEditPar();
      }

      $scope.checkForClashingName = function(scenario) {
        function hasClash(s) {
          return s.name == scenario.name && s.id != scenario.id;
        }

        return _.some(scenarios, hasClash);
      };

      var initNewScenario = function() {
        $scope.scenario.active = true;
        $scope.scenario.id = null;
        $scope.scenario.progset_id = null;
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.pars = [];
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while ($scope.checkForClashingName(scenario));
      };

      $scope.getParsInScenario = function () {
        var parsets = $scope.parsets;
        var parset_id = $scope.scenario.parset_id;
        if (parset_id) {
          parsets = _.filter($scope.parsets, { id: parset_id });
        };
        if (parsets.length > 0) {
          return _.filter(parsets[0].pars[0], { visible: 1 });
        }
        return [];
      };

      $scope.getLongParName = function (short) {
        var pars = $scope.getParsInScenario();
        var par = _.findWhere(pars, { short: short });
        return par ? par.name : '';
      };

      $scope.getPopsOfPar = function () {
        var parName = $scope.editPar.name;
        if (ykeys.hasOwnProperty($scope.scenario.parset_id)) {
          var ykeysOfParset = ykeys[$scope.scenario.parset_id];
          if (ykeysOfParset.hasOwnProperty(parName)) {
            var result = ykeysOfParset[parName];
            var tot = _.findWhere(result, {'val': 'tot'});
            if (tot) {
              tot["label"] = "Total Population";
            }
            return result;
          }
        }
        return [];
      };

      $scope.selectNewPar = function () {
        var pops = $scope.getPopsOfPar();
        console.log('pops', JSON.stringify(pops));
        $scope.editPar.for = pops[0].val;
        $scope.editPar.startval = pops[0].limits[0];
        $scope.editPar.endval = pops[0].limits[1];
        $scope.editPar.startyear = years[0];
        var n = years.length;
        $scope.editPar.endyear = years[n-1];
        console.log($scope.editPar.for);
        console.log('new', $scope.editPar.name, '->', _.pluck(pops, 'val'))
      };

      var resetEditPar = function () {
        $scope.editPar = { 'name': $scope.getParsInScenario()[0].short };
        $scope.selectNewPar();
      };

      $scope.addPar = function () {
        $scope.scenario.pars.push($scope.editPar);
        resetEditPar();
      };

      $scope.removePar = function (i) { $scope.scenario.pars.splice(i, 1); };

      $scope.isEditInvalid = function () {
        function isValidKey(k) { return !_.isFinite($scope.editPar[k]) }
        return _.some(_.map(editKeys, isValidKey));
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      $scope.save = function () {
        $modalInstance.close($scope.scenario); };

      initialize();

    });
});
