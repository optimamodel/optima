define([
  'angular',
  'ui.router',
  './parameter-scenarios-modal',
  './program-scenarios-modal'
], function (angular) {

  'use strict';

  var module = angular.module(
    'app.scenarios',
    [
      'ui.router',

      // import the controllers for the modals
      'app.program-scenarios-modal',
      'app.parameter-scenarios-modal']);


  module.config(function ($stateProvider) {
      $stateProvider
        .state('scenarios', {
          url: '/scenarios',
          templateUrl: 'js/modules/scenarios/scenarios.html?cacheBust=xxx' ,
          controller: 'AnalysisScenariosController'
        });
    });

  
  module.controller('AnalysisScenariosController', function (
      $scope, $modal, $state, projectService, modalService, toastr, rpcService) {

    function initialize() {
      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined($scope.project) && ($scope.project.id !== projectService.project.id)) {
          reloadActiveProject();
        }
      });
      reloadActiveProject();
    }

    function reloadActiveProject() {
      projectService
        .getActiveProject()
        .then(function(response) {
          $scope.project = response.data;
          $scope.state = {
            start: $scope.project.startYear,
            end: $scope.project.endYear,
          };
          $scope.years = _.range($scope.project.startYear, $scope.project.endYear+21);
          $scope.isMissingData = !$scope.project.calibrationOK;

          return rpcService.rpcRun('load_parset_summaries', [$scope.project.id]);
        })
        .then(function(parsetResponse) {
          $scope.parsets = parsetResponse.data.parsets;

          return rpcService.rpcRun('load_progset_summaries', [$scope.project.id]);
        })
        .then(function(progsetsResponse) {
          $scope.progsets = progsetsResponse.data.progsets;
          $scope.anyOptimizable = $scope.project.costFuncsOK;
        })
        .then(function () {
          return rpcService.rpcRun('load_scenario_summaries', [$scope.project.id]);
        })
        .then(function(scenariosResponse) {
          console.log("scenarios response", scenariosResponse.data);
          $scope.parametersByParsetId = scenariosResponse.data.ykeysByParsetId;
          $scope.budgetsByProgsetId = scenariosResponse.data.defaultBudgetsByProgsetId;
          $scope.defaultCoveragesByParsetIdyProgsetId = scenariosResponse.data.defaultCoveragesByParsetIdyProgsetId;
          loadScenarios(scenariosResponse.data.scenarios);
          $scope.graphScenarios(false);
        });
    }

    function loadScenarios(scenarios) {
      $scope.scenarios = scenarios;
      function returnName(s) { return s.name }
      $scope.scenarios = _.sortBy($scope.scenarios, returnName);
      console.log("loading scenarios", $scope.scenarios);
    }

    $scope.saveScenarios = function(scenarios, successMsg) {
      delete $scope.state.graphs;
      console.log("saving scenarios", scenarios);
      rpcService.rpcRun(
        'save_scenario_summaries', [$scope.project.id, scenarios])
      .then(function (response) {
        loadScenarios(response.data.scenarios);
        if (successMsg) {
          toastr.success(successMsg)
        }
      });
    };

    $scope.downloadScenario = function(scenario) {
      rpcService
        .rpcDownload(
          'download_project_object',
          [projectService.project.id, 'scenario', scenario.id])
        .then(function(response) {
          toastr.success('Scenario downloaded');
        });

    };

    $scope.uploadScenario = function(scenario) {
      rpcService
        .rpcUpload(
          'upload_project_object', [projectService.project.id, 'scenario'], {}, '.scn')
        .then(function(response) {
		  if (response.data.name == 'BadFileFormatError') {
			toastr.error('The file you have chosen is not valid for uploading');  
		  } else {
            toastr.success('Scenario uploaded');
            $state.reload() }
        });
    };

    function getSelectors() {
      function getChecked(s) { return s.checked; }
      function getKey(s) { return s.key }
      var scope = $scope;
      var which = [];
      if (scope.graphs) {
        if (scope.graphs.advanced) {
          which.push('advanced');
        }
        var selectors = scope.graphs.selectors;
        if (selectors) {
          which = which.concat(_.filter(selectors, getChecked).map(getKey));
        }
      }
      return which;
    }

    $scope.graphScenarios = function(isRun) {
      if (_.isUndefined(isRun)) {
        isRun = false;
      }
      delete $scope.graphs;
      rpcService
        .rpcRun(
          'make_scenarios_graphs',
          [$scope.project.id],
          {
            which: getSelectors(),
            is_run: isRun,
            startYear: $scope.state.start,
            endYear: $scope.state.end
          })
        .then(function(response) {
          $scope.state.graphs = response.data.graphs;
          toastr.success('Loaded graphs');
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
        templateUrl = 'js/modules/scenarios/program-scenarios-modal.html?cacheBust=xxx';
        controller = 'ProgramScenariosModalController';
      } else  {
        templateUrl = 'js/modules/scenarios/parameter-scenarios-modal.html?cacheBust=xxx';
        controller = 'ParameterScenariosModalController';
      }
      return $modal.open({
        templateUrl: templateUrl,
        controller: controller,
        windowClass: 'fat-modal',
        resolve: {
          project: function() { return $scope.project },
          scenarios: function () { return $scope.scenarios; },
          scenario: function () { return angular.copy(scenario); },
          parsets: function () { return $scope.parsets; },
          progsets: function () { return $scope.progsets; },
          parsByParsetId: function () { return $scope.parametersByParsetId; },
          budgetsByProgsetId: function() { return $scope.budgetsByProgsetId; },
          coveragesByParsetIdyProgsetId: function() { return $scope.defaultCoveragesByParsetIdyProgsetId; },
          years: function() { return $scope.years }
        }
      });
    }

    function deepCopyJson(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
    }

    /**
     * Opens a scenario model in different modes
     * @param {string} action: 'add', 'edit' 'delete'
     */
    $scope.openModal = function (scenario, action, $event) {

      if ($event) {
        $event.preventDefault();
      }

      var newScenarios = deepCopyJson($scope.scenarios);

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
          .then(function(scenario) {
            newScenarios[iScenario] = scenario;
            newScenarios[iScenario].active = true;
            $scope.saveScenarios(newScenarios, "Saved changes");
          });

      } else if (action === 'copy') {

        var newScenario = deepCopyJson(scenario);
        var otherNames = _.pluck($scope.scenarios, 'name');
        newScenario.name = rpcService.getUniqueName(
          scenario.name, otherNames);
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

  return module;
});
