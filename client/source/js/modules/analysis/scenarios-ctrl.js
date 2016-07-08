
define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisScenariosController', function (
      $scope, $http, $modal, meta, info, scenarioParametersResponse,
      progsetsResponse, parsetResponse, scenariosResponse, toastr) {

    var project = info.data;
    var parsets = parsetResponse.data.parsets;
    var progsets = progsetsResponse.data.progsets;

    function initialize() {
      loadScenarios(scenariosResponse.data.scenarios);
      $scope.ykeys = scenariosResponse.data.ykeysByParsetId;
      console.log("parameterKeys", $scope.ykeys);
      $scope.isMissingModelData = !project.has_data;
      $scope.isMissingProgramSet = progsets.length == 0;
    }

    function loadScenarios(scenarios) {
      $scope.scenarios = scenarios;
      $scope.scenarios = _.sortBy($scope.scenarios, function(scenario) {
        return scenario.name;
      });
      console.log("loading scenarios", $scope.scenarios);
    }

    $scope.saveScenarios = function(scenarios, success_msg) {
      console.log("saving scenarios", scenarios);
      $http.put(
        '/api/project/' + project.id + '/scenarios',
        {'scenarios': scenarios })
      .success(function (response) {
        loadScenarios(response.scenarios);
        if (success_msg) {
          toastr.success(success_msg)
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

    function getSelectors() {
      if ($scope.graphs) {
        var selectors = $scope.graphs.selectors;
        if (selectors) {
          var which = _.filter(selectors, function(selector) {
            return selector.checked;
          })
          .map(function(selector) {
            return selector.key;
          });
          console.log('which', which)
          if (which.length > 0) {
            return which;
          }
        }
      }
      return null;
    }

    $scope.updateGraphs = function() {
      $http.post(
        '/api/project/' + project.id + '/scenarios/results',
        {which: getSelectors()})
      .success(function (data) {
        $scope.graphs = data.graphs;
      });
    };

    $scope.isRunnable = function () {
      return _.some($scope.scenarios, function(s) { return s.active });
    };

    $scope.parsetName = function (scenario) {
      var parset = _.findWhere(parsets, {id: scenario.parset_id});
      return parset ? parset.name : 'N/A';
    };

    $scope.programSetName = function (scenario) {
      var progset = _.findWhere(progsets, {id: scenario.progset_id});
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
          parsets: function () { return parsets; },
          progsets: function () { return progsets; },
          ykeys: function () { return $scope.ykeys; }
        }
      });
    }

    /**
     * Function opens a model in different modes
     * @param {string} action: 'add', 'edit' 'delete'
     */
    $scope.modal = function (scenario, action, $event) {
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
              console.log('new scenario')
              var i = newScenarios.indexOf(_.findWhere(newScenarios, { id: scenario.id }));
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

        var scenario = _.findWhere(newScenarios, { id: scenario.id });
        $scope.saveScenarios(_.without(newScenarios, scenario), "Deleted scenario");

      }
    };

    initialize();

  });

});
