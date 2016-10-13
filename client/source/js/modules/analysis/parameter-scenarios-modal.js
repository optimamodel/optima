define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
        $scope, $modalInstance, scenarios, scenario, parsets,
        progsets, ykeys, years) {

      function initialize() {
        $scope.parsets = parsets;
        $scope.progsets = progsets;
        $scope.otherNames = _.without(_.pluck(scenarios, 'name'), scenario.name);
        $scope.scenario = scenario;
        $scope.years = years;
        $scope.defaultPars = ykeys;
        $scope.state = {};

        if (_.isUndefined($scope.scenario.name)) {
          initNewScenario();
        }

        $scope.selectParset();
        buildPopsOfPar();
      }

      $scope.selectParset = function() {
        var parset_id = $scope.scenario.parset_id;
        $scope.state.parset = _.findWhere($scope.parsets, { id: parset_id });
        $scope.parsInScenario = _.filter($scope.state.parset.pars[0], {visible: 1 });
      };

      $scope.isNameClash = function(scenario_name) {
        return _.contains($scope.otherNames, scenario_name);
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
        } while ($scope.isNameClash(scenario.name));

      };

      function buildPopsOfPar() {
        console.log('buildPopsOfPar')
        $scope.popsOfPar = [];
        _.each($scope.scenario.pars, function(par) {
          var parName = par.name;
          var year = par.startyear;
          var pops = [];
          var defaultPars = $scope.defaultPars[$scope.scenario.parset_id][year];
          if (defaultPars.hasOwnProperty(parName)) {
            pops = defaultPars[parName];
            var totalPop = _.findWhere(pops, {'val': 'tot'});
            if (totalPop) {
              totalPop["label"] = "Total Population";
            }
            if (_.isUndefined(par.forLabel)) {
              var pop = _.find(pops, function(pop) {
                return "" + pop.val == "" + par.for;
              });
              if (pop) {
                par.forLabel = pop.label;
              }
            }
          }
          $scope.popsOfPar.push(pops);
        });
        console.log('new $scope.popsOfPar', $scope.popsOfPar);
      }

      $scope.selectNewPar = function (iPar) {
        buildPopsOfPar();
        var par = $scope.scenario.pars[iPar];
        var pops = $scope.popsOfPar[iPar];
        par.for = $scope.popsOfPar[iPar][0].val;
        var labels = _.pluck(pops, "label");
        if (!_.contains(labels, par.forLabel)) {
          par.forLabel = labels[0];
        }
        par.startval = $scope.popsOfPar[iPar][0].startval;
      };

      $scope.selectNewPop = function (iPar) {
        var par = $scope.scenario.pars[iPar];
        var popsOfPar = $scope.popsOfPar[iPar];
        var pop = _.findWhere(popsOfPar, {label: par.forLabel});
        par.startval = pop.startval;
      };

      $scope.selectNewYear = function (iPar) {
        var par = $scope.scenario.pars[iPar];
        buildPopsOfPar();
        var popsOfPar = $scope.popsOfPar[iPar];
        var pop = _.findWhere(popsOfPar, {label: par.forLabel});
        par.startval = pop.startval;
      };

      $scope.addPar = function () {
        var newPar = { 'name': $scope.parsInScenario[0].short };
        newPar.endval = null;
        newPar.startyear = new Date().getFullYear();
        newPar.endyear = null;
        $scope.scenario.pars.push(newPar);
        var nPar = $scope.scenario.pars.length;
        $scope.selectNewPar(nPar - 1);
        console.log('newPar', newPar);
      };

      $scope.removePar = function (i) {
        $scope.scenario.pars.splice(i, 1);
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
