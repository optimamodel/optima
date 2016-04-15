
define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisScenariosController', function (
      $scope, $http, $modal, meta, info, scenarioParametersResponse, progsetsResponse,
      parsetResponse, scenariosResponse) {

    var project = info.data;
    var parsets = parsetResponse.data.parsets;
    var progsets = progsetsResponse.data.progsets;

    $scope.scenarios = scenariosResponse.data.scenarios;
    $scope.isMissingModelData = !project.has_data;
    $scope.isMissingProgramSet = progsets.length == 0;

    $scope.alerts = [];

    var killOldestAlert = function() {
      if ($scope.alerts.length > 0) {
        $scope.alerts.shift();
        $scope.$apply();
      }
    }

    var addTimedAlert = function(msg) {
      $scope.alerts.push({ msg: msg });
      setTimeout(killOldestAlert, 3000);
    };

    var saveScenarios = function (scenarios, msg) {
      $http
        .put('/api/project/' + project.id + '/scenarios', {'scenarios': scenarios })
        .success(function (response) {
          $scope.scenarios = response.scenarios;
          if (msg) { addTimedAlert(msg) }
        });
    };

    var openScenarioModal = function (scenario) {
      var templateUrl, controller;
      var scenario_type = scenario.scenario_type;
      if ((scenario_type === "budget" ) || (scenario_type === 'coverage')) {
        templateUrl = 'js/modules/analysis/program-scenarios-modal.html';
        controller = 'ProgramScenariosModalController';
      } else  {
        templateUrl = 'js/modules/analysis/parameter-scenarios-modal.html';
        controller = 'ParameterScenariosModalController';
      }
      var ykeys = $http.get('/api/project/' + project.id + '/parsets/ykeys');
      return $modal.open({
        templateUrl: templateUrl,
        controller: controller,
        windowClass: 'fat-modal',
        resolve: {
          scenarios: function () { return $scope.scenarios; },
          scenario: function () { return angular.copy(scenario); },
          parsets: function () { return parsets; },
          progsets: function () { return progsets; },
          ykeys: function () { return ykeys; },
        }
      });

    };

    $scope.runScenarios = function () {
      $http
        .get('/api/project/' + project.id + '/scenarios/results')
        .success(function (data) { $scope.graphs = data; });
    };

    $scope.isRunnable = function () {
      return _.filter($scope.scenarios, { active: true }).length > 0;
    };

    $scope.parsetName = function (scenario) {
      var theseParsets = _.filter(parsets, {id: scenario.parset_id});
      return theseParsets.length > 0 ? theseParsets[0].name : '';
    };

    $scope.programSetName = function (scenario) {
      var theseProgsets = _.filter(progsets, {id: scenario.progset_id});
      return theseProgsets.length > 0 ? theseProgsets[0].name : '';
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
              saveScenarios(newScenarios, "Created scenario");
            });

      } else if (action === 'edit') {

        return openScenarioModal(scenario)
          .result
          .then(
            function (scenario) {
              var i = newScenarios.indexOf(_.findWhere(newScenarios, { name: scenario.name }));
              newScenarios[i] = scenario;
              newScenarios[i].active = true;
              saveScenarios(newScenarios, "Saved changes");
            });

      } else if (action === 'copy') {

        var newScenario = angular.copy(scenario);
        newScenario.name = scenario.name + ' Copy';
        newScenario.id = null;
        newScenarios.push(newScenario);
        saveScenarios(newScenarios, "Copied scenario");

      } else if (action === 'delete') {

        var scenario = _.findWhere(newScenarios, { name: scenario.name });
        saveScenarios(
            _.without(newScenarios, scenario), "Deleted scenario");

      }
    };

  });

});
