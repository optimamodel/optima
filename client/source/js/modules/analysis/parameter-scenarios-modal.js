define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
        $scope, $modalInstance, scenarios, scenario, parsets,
        progsets, ykeys, years) {

      function initialize() {
        $scope.scenario = scenario;
        $scope.parsets = parsets;
        $scope.progsets = progsets;
        if (_.isUndefined($scope.scenario.name)) {
          initNewScenario();
        }
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
        }
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

      $scope.getPopsOfPar = function (iPar) {
        var parName = $scope.scenario.pars[iPar].name;
        console.log('par.for', $scope.scenario.pars[iPar].for);
        if (ykeys.hasOwnProperty($scope.scenario.parset_id)) {
          var ykeysOfParset = ykeys[$scope.scenario.parset_id];
          if (ykeysOfParset.hasOwnProperty(parName)) {
            var result = ykeysOfParset[parName];
            console.log('yekys', result);
            var tot = _.findWhere(result, {'val': 'tot'});
            if (tot) {
              tot["label"] = "Total Population";
            }
            return result;
          }
        }
        return [];
      };

      $scope.selectNewPar = function (iPar) {
        var par = $scope.scenario.pars[iPar];
        var pops = $scope.getPopsOfPar(iPar);
        if (_.indexOf(_.pluck(pops, 'val', par.for) < 0)) {
          par.for = pops[0].val;
        }
      };

      $scope.addPar = function () {
        var newPar = { 'name': $scope.getParsInScenario()[0].short };
        $scope.scenario.pars.push(newPar);
        var iLast = $scope.scenario.pars.length - 1;
        $scope.selectNewPar(iLast);
        var pops = $scope.getPopsOfPar(iLast);
        newPar.startval = pops[0].limits[0];
        newPar.endval = pops[0].limits[1];
        newPar.startyear = new Date().getFullYear();
        newPar.endyear = years[years.length-1];
        console.log('new', newPar.name, '->', _.pluck(pops, 'val'))
      };

      $scope.removePar = function (i) { $scope.scenario.pars.splice(i, 1); };

      $scope.isEditInvalid = function () {
        var editKeys = ['startval', 'endval', 'startyear', 'endyear'];
        function isValidKey(k) { return !_.isFinite($scope.editPar[k]) }
        return _.some(_.map(editKeys, isValidKey));
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      $scope.save = function () {
        $modalInstance.close($scope.scenario); };

      initialize();

    });
});
