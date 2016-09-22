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
        var filteredParsets = $scope.parsets;
        var parset_id = $scope.scenario.parset_id;
        if (parset_id) {
          filteredParsets = _.filter($scope.parsets, { id: parset_id });
        }
        $scope.parsInScenario = [];
        if (parsets.length > 0) {
          $scope.parsInScenario = _.filter(filteredParsets[0].pars[0], { visible: 1 });
        }

        $scope.buildPopsOfPar();
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

      $scope.buildPopsOfPar = function () {
        $scope.popsOfPar = [];
        _.each($scope.scenario.pars, function(par) {
          var parName = par.name;
          var popsInPar = [];
          if (ykeys.hasOwnProperty($scope.scenario.parset_id)) {
            var ykeysOfParset = ykeys[$scope.scenario.parset_id];
            if (ykeysOfParset.hasOwnProperty(parName)) {
              popsInPar = ykeysOfParset[parName];
              var tot = _.findWhere(popsInPar, {'val': 'tot'});
              if (tot) {
                tot["label"] = "Total Population";
              }
              var pop = _.find(popsInPar, function(pop) {
                return "" + pop.val == "" + par.for;
              });
              if (pop) {
                par.forLabel = pop.label;
              }
            }
          }
          $scope.popsOfPar.push(popsInPar);
        });
        console.log('$scope.popsOfPar', $scope.popsOfPar);
      };

      $scope.selectNewPar = function (iPar) {
        $scope.buildPopsOfPar();
        var par = $scope.scenario.pars[iPar];
        var pops = $scope.popsOfPar[iPar];
        var labels = _.pluck(pops, "label");
        if (!_.contains(labels, par.forLabel)) {
          par.forLabel = labels[0];
        }
      };

      $scope.addPar = function () {
        var newPar = { 'name': $scope.parsInScenario[0].short };
        $scope.scenario.pars.push(newPar);
        var iLast = $scope.scenario.pars.length - 1;
        $scope.selectNewPar(iLast);
        $scope.buildPopsOfPar();
        newPar.for = $scope.popsOfPar[iLast][0].val;
        newPar.startval = $scope.popsOfPar[iLast][0].limits[0];
        newPar.endval = $scope.popsOfPar[iLast][0].limits[1];
        newPar.startyear = new Date().getFullYear();
        newPar.endyear = years[years.length-1];
        console.log('new', newPar.name, '->', _.pluck($scope.popsOfPar, 'val'))
      };

      $scope.removePar = function (i) { $scope.scenario.pars.splice(i, 1); };

      $scope.isEditInvalid = function () {
        var editKeys = ['startval', 'endval', 'startyear', 'endyear'];
        function isValidKey(k) { return !_.isFinite($scope.editPar[k]) }
        return _.some(_.map(editKeys, isValidKey));
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      $scope.save = function () {
        _.each($scope.scenario.pars, function(par, iPar) {
          var pops = $scope.popsOfPar[iPar];
          var pop = _.findWhere(pops, {label: par.forLabel});
          delete par.forLabel;
          par.for = pop.val;
        });
        console.log('save scenario', JSON.stringify($scope.scenario, null, 2));
        $modalInstance.close($scope.scenario); };

      initialize();

    });
});
