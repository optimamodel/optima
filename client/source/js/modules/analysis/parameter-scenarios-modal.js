define(['angular'], function (module) {

  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function (
        $scope, $modalInstance, scenarios, scenario, parsets,
        progsets, parsByIdAndYear, years) {

      function initialize() {
        $scope.parsets = parsets;
        $scope.progsets = progsets;
        $scope.scenario = scenario;
        $scope.years = years;
        $scope.parsByIdAndYear = parsByIdAndYear;

        console.log('scenario', scenario);
        console.log('parsByIdAndYear', $scope.parsByIdAndYear);

        $scope.state = {};

        if (_.isUndefined($scope.scenario.name)) {
          initNewScenario();
        }

        $scope.selectParset();
        buildPopsOfPar();
      }

      $scope.selectParset = function() {
        $scope.state.parset = _.findWhere(
          $scope.parsets, { id: $scope.scenario.parset_id });
      };

      var initNewScenario = function() {
        $scope.scenario.active = true;
        $scope.scenario.id = null;
        $scope.scenario.progset_id = null;
        $scope.scenario.parset_id = $scope.parsets[0].id;
        $scope.scenario.pars = [];
        var otherNames = _.without(_.pluck(scenarios, 'name'), scenario.name);
        var i = 1;
        do {
          $scope.scenario.name = "Scenario " + i;
          i += 1;
        } while (_.contains(otherNames, scenario.name));

      };

      function buildPopsOfPar() {
        $scope.popsOfPar = [];
        $scope.parSelectors = [];

        _.each($scope.scenario.pars, function(scenPar) {
          var scenParName = scenPar.name;
          var year = scenPar.startyear;
          var pars = $scope.parsByIdAndYear[$scope.scenario.parset_id][year];

          $scope.parSelectors = [];

          var popsOfPar = [];
          _.each(pars, function(par) {

            $scope.parSelectors.push({name: par.name, short: par.short});

            if (par.short == scenParName) {
              if (par.pop == "tot") {
                par.popLabel = "Total Population";
                scenPar.forLabel = "Total Population";
              } else if ("" + par.pop == "" + scenPar.for) {
                scenPar.forLabel = par.popLabel;
              }
              popsOfPar.push(par);
            }
          });

          $scope.parSelectors = _.uniq($scope.parSelectors, function(par) { return par.short + par.name; });
          $scope.popsOfPar.push(popsOfPar);

        });

        console.log('$scope.scenario.pars', $scope.scenario.pars);
        console.log('$scope.popsOfPar', $scope.popsOfPar);
        console.log('$scope.parSelectors', $scope.parSelectors);
      }

      $scope.selectNewPar = function (iPar) {
        buildPopsOfPar();
        var scenPar = $scope.scenario.pars[iPar];
        var pops = $scope.popsOfPar[iPar];
        scenPar.for = $scope.popsOfPar[iPar][0].pop;
        var popLabels = _.pluck(pops, "popLabel");
        if (!_.contains(popLabels, scenPar.forLabel)) {
          scenPar.forLabel = popLabels[0];
        }
        scenPar.startval = $scope.popsOfPar[iPar][0].startval;
      };

      $scope.resetStartValue = function (iPar) {
        var scenPar = $scope.scenario.pars[iPar];
        var pops = $scope.popsOfPar[iPar];
        console.log('scenPar, pops', scenPar, pops);
        var pop = _.findWhere(pops, {popLabel: scenPar.forLabel});
        console.log('pop', pop);
        scenPar.startval = pop.startval;
      };

      $scope.selectNewYear = function (iPar) {
        buildPopsOfPar();
        $scope.resetStartValue(iPar);
      };

      $scope.addPar = function () {
        var newScenPar = {}
        newScenPar.endval = null;
        newScenPar.startyear = new Date().getFullYear();
        newScenPar.endyear = null;
        var pars = $scope.parsByIdAndYear[$scope.scenario.parset_id][newScenPar.startyear];
        newScenPar.name =  pars[0].short;
        $scope.scenario.pars.push(newScenPar);
        var nPar = $scope.scenario.pars.length;
        $scope.selectNewPar(nPar - 1);
        console.log('newScenPar', newScenPar);
      };

      $scope.removePar = function (i) {
        $scope.scenario.pars.splice(i, 1);
      };

      $scope.cancel = function () { $modalInstance.dismiss("cancel"); };

      $scope.save = function () {
        _.each($scope.scenario.pars, function(scenPar, iPar) {
          var pops = $scope.popsOfPar[iPar];
          var pop = _.findWhere(pops, {popLabel: scenPar.forLabel});
          delete scenPar.forLabel;
          scenPar.for = pop.pop;
        });
        console.log('save scenario', JSON.stringify($scope.scenario, null, 2));
        $modalInstance.close($scope.scenario); };

      initialize();

    });
});
