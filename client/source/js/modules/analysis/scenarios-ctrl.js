
define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisScenariosController', function (
      $scope, $http, $modal, meta, info, scenarioParametersResponse, progsetsResponse,
      parsetResponse, scenariosResponse, toastr) {

    var project = info.data;
    var parsets = parsetResponse.data.parsets;
    var progsets = progsetsResponse.data.progsets;

    function initialize() {

      $scope.scenarios = scenariosResponse.data.scenarios;
      sort_scenarios();
      console.log("loading scenarios", scenariosResponse.data);

      $scope.ykeys = scenariosResponse.data.ykeysByParsetId;
      console.log("loading ykeys", $scope.ykeys);

      $scope.isMissingModelData = !project.hasData;
      $scope.isMissingProgramSet = progsets.length == 0;
    }

    function sort_scenarios() {
      $scope.scenarios = _.sortBy($scope.scenarios, function(scenario) {
        return scenario.name;
      });
      console.log('Sorting scenarios');
    }

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    $scope.saveScenarios = function(scenarios, msg) {
      consoleLogJson("saving scenarios", scenarios);
      $http.put(
        '/api/project/' + project.id + '/scenarios',
        {'scenarios': scenarios })
      .success(function (response) {
        $scope.scenarios = response.scenarios;
        sort_scenarios();
        consoleLogJson("returned scenarios", $scope.scenarios);
        if (msg) {
          toastr.success(msg)
        }
      });
    };

    $scope.runScenarios = function () {
      $http.get(
        '/api/project/' + project.id + '/scenarios/results')
      .success(function (data) {
        $scope.graphs = data.graphs;
      });
    };

    $scope.isRunnable = function () {
      return _.some($scope.scenarios, function(s) { return s.active });
    };

    $scope.parsetName = function (scenario) {
      var parset = _.findWhere(parsets, {id: scenario.parset_id});
      return parset ? parset.name : '';
    };

    $scope.programSetName = function (scenario) {
      var progset = _.findWhere(progsets, {id: scenario.progset_id});
      return progset ? progset.name : '';
    };

    function openScenarioModal(scenario) {
      var templateUrl, controller;
      var scenario_type = scenario.scenario_type;
      if ((scenario_type === "budget" ) || (scenario_type === 'coverage')) {
        templateUrl = 'js/modules/analysis/program-scenarios-modal.html';
        controller = 'ProgramScenariosModalController';
      } else  {
        templateUrl = 'js/modules/analysis/parameter-scenarios-modal.html';
        controller = 'ParameterScenariosModalController';
      }
      return $modal.open({
        templateUrl: templateUrl,
        controller: controller,
        windowClass: 'fat-modal',
        resolve: {
          scenarios: function () { return $scope.scenarios; },
          scenario: function () { return angular.copy(scenario); },
          parsets: function () { return parsets; },
          progsets: function () { return progsets; },
          ykeys: function () { return $scope.ykeys; }
        }
      });
    };

    $scope.modal = function (scenario, action, $event) {
      // action: 'add', 'edit', 'delete'

      if ($event) {
        $event.preventDefault();
      }

      var newScenarios = angular.copy($scope.scenarios);

      if (action === 'add') {

        return openScenarioModal(scenario)
          .result
          .then(
            function (scenario) {
              newScenarios.push(scenario);
              $scope.saveScenarios(newScenarios, "Created scenario");
            });

      } else if (action === 'edit') {

        return openScenarioModal(scenario)
          .result
          .then(
            function (scenario) {
              var i = newScenarios.indexOf(_.findWhere(newScenarios, { name: scenario.name }));
              newScenarios[i] = scenario;
              newScenarios[i].active = true;
              $scope.saveScenarios(newScenarios, "Saved changes");
            });

      } else if (action === 'copy') {

        var newScenario = angular.copy(scenario);
        newScenario.name = scenario.name + ' Copy';
        newScenario.id = null;
        newScenarios.push(newScenario);
        $scope.saveScenarios(newScenarios, "Copied scenario");

      } else if (action === 'delete') {

        var scenario = _.findWhere(newScenarios, { name: scenario.name });
        $scope.saveScenarios(_.without(newScenarios, scenario), "Deleted scenario");

      }
    };

    initialize();

  });

});
