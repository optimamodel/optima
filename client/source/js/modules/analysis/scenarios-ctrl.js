
define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisScenariosController', function (
      $scope, $http, $modal, info, progsetsResponse, parsetResponse,
      scenariosResponse, toastr) {

    function initialize() {
      $scope.project = info.data;
      $scope.parsets = parsetResponse.data.parsets;
      $scope.progsets = progsetsResponse.data.progsets;
      $scope.parametersByParsetId = scenariosResponse.data.ykeysByParsetId;
      $scope.budgetsByProgsetId = scenariosResponse.data.defaultBudgetsByProgsetId;
      $scope.defaultCoveragesByParsetIdyProgsetId = scenariosResponse.data.defaultCoveragesByParsetIdyProgsetId;
      $scope.years = scenariosResponse.data.years;
      $scope.isMissingData = !$scope.project.hasParset;
      $scope.isOptimizable = $scope.project.isOptimizable;
      $scope.isMissingProgramSet = $scope.project.nProgram == 0;
      loadScenarios(scenariosResponse.data.scenarios);
    }

    function loadScenarios(scenarios) {
      $scope.scenarios = scenarios;
      function returnName(s) { return s.name }
      $scope.scenarios = _.sortBy($scope.scenarios, returnName);
      console.log("loading scenarios", $scope.scenarios);
    }

    $scope.saveScenarios = function(scenarios, successMsg) {
      console.log("saving scenarios", scenarios);
      $http.put(
        '/api/project/' + $scope.project.id + '/scenarios',
        {'scenarios': scenarios })
      .success(function (response) {
        loadScenarios(response.scenarios);
        if (successMsg) {
          toastr.success(successMsg)
        }
      });
    };

    $scope.runScenarios = function () {
      $scope.graphs = {};
      $http.get(
        '/api/project/' + $scope.project.id + '/scenarios/results')
      .success(function (data) {
        $scope.graphs = data.graphs;
      });
    };

    $scope.isRunnable = function () {
      return _.some($scope.scenarios, function(s) { return s.active });
    };

    $scope.getParsetName = function (scenario) {
      var parset = _.findWhere($scope.parsets, {id: scenario.parset_id});
      return parset ? parset.name : 'N/A';
    };

    $scope.getProgramSetName = function (scenario) {
      var progset = _.findWhere($scope.progsets, {id: scenario.progset_id});
      return progset ? progset.name : 'N/A';
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
          parsets: function () { return $scope.parsets; },
          progsets: function () { return $scope.progsets; },
          ykeys: function () { return $scope.parametersByParsetId; },
          budgetsByProgsetId: function() { return $scope.budgetsByProgsetId; },
          coveragesByParsetIdyProgsetId: function() { return $scope.defaultCoveragesByParsetIdyProgsetId; },
          years: function() { return $scope.years }
        }
      });
    }

    /**
     * Opens a scenario model in different modes
     * @param {string} action: 'add', 'edit' 'delete'
     */
    $scope.openModal = function (scenario, action, $event) {

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

        scenario = _.findWhere(newScenarios, {name: scenario.name});
        var iScenario = _.indexOf(newScenarios, scenario);

        return openScenarioModal(scenario)
          .result
          .then(
            function (scenario) {
              newScenarios[iScenario] = scenario;
              newScenarios[iScenario].active = true;
              $scope.saveScenarios(newScenarios, "Saved changes");
            });

      } else if (action === 'copy') {

        var newScenario = angular.copy(scenario);
        newScenario.name = scenario.name + ' Copy';
        newScenario.id = null;
        newScenarios.push(newScenario);
        $scope.saveScenarios(newScenarios, "Copied scenario");

      } else if (action === 'delete') {

        var deleteScenario = _.findWhere(newScenarios, { id: scenario.id });
        $scope.saveScenarios(
            _.without(newScenarios, deleteScenario), "Deleted scenario");

      }
    };

    initialize();

  });

});
