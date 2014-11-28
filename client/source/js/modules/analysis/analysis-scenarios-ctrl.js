define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta, scenarioParamsResponse) {

        var linesGraphOptions, linesGraphData, responseData, availableScenarioParams;

        // initialize all necessary data for this controller
        var initialize = function() {

          availableScenarioParams = scenarioParamsResponse.data.params;

          $scope.scenarios = [
            {'name':'Current conditions', 'pars':[]},
            {"name": '100% condom use in KAPs', 'pars': [
              { keys: ['condom','reg'], pop: 0, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { keys: ['condom','cas'], pop: 0, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { keys: ['condom','com'], pop: 1, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { keys: ['condom','com'], pop: 5, startyear: 2010, endyear: 2015, startval: -1, endval: 1}
            ]}
          ];

          $scope.runScenariosOptions = {
            scenarios: $scope.scenarios,
            dosave: false
          };

          $scope.types = [
            { id: 'prev', name: 'Prevalence', active: true, byPopulation: true, total: false },
            { id: 'daly', name: 'DALYs', active: false, byPopulation: false, total: false },
            { id: 'death', name: 'Deaths', active: false, byPopulation: false, total: false },
            { id: 'inci', name: 'New infections', active: false, byPopulation: false, total: false },
            { id: 'dx', name: 'Diagnoses', active: false, byPopulation: false, total: false },
            { id: 'tx1', name: 'First-line treatment', active: false, byPopulation: false, total: false },
            { id: 'tx2', name: 'Second-line treatment', active: false, byPopulation: false, total: false }
          ];


          linesGraphOptions = {
            height: 250,
            width: 400,
            margin: {
              top: 20,
              right: 20,
              bottom: 60,
              left: 100
            },
            xAxis: {
              axisLabel: 'Year',
              tickFormat: function (d) {
                return d3.format('d')(d);
              }
            },
            yAxis: {
              axisLabel: '',
              tickFormat: function (d) {
                return d3.format(',.2f')(d);
              }
            }
          };

          linesGraphData = {
            lines: [],
            scatter: []
          };
        };

        /*
        * Returns an array containing arrays with [x, y] for d3 line data.
        */
        var generateLineData = function(xData, yData) {
          return _(yData).map(function (value, i) {
            return [xData[i], value];
          });
        };

        /*
        * Returns an graph based on the provided yData.
        *
        * yData should be an array where each entry contains an array of all
        * y-values from one line.
        */
        var generateGraph = function(type, yData, xData, title) {
          var graph = {
            options: angular.copy(linesGraphOptions),
            data: angular.copy(linesGraphData),
            type: type,
            title: title
          };

          _(yData).each(function(lineData) {
            graph.data.lines.push(generateLineData(xData, lineData));
          });

          return graph;
        };

        /*
         * Regenerate graphs based on the response and type settings in the UI.
         */
        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }

          var graphs = [];

          _($scope.types).each(function (type) {

            var data = response[type.id];

            // generate graphs showing the overall data for this type
            if (type.total) {
              var title = 'Showing total data for "' + type.name + '"';
              var graph = generateGraph(type, data.tot.data, response.tvec.np_array, title);
              graph.options.xAxis.axisLabel = data.xlabel;
              graph.options.yAxis.axisLabel = data.ylabel;
              graphs.push(graph);
            }

            // generate graphs for this type for each population
            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {
                var title = 'Showing ' + type.name + ' for population "' + meta.pops.long[populationIndex] + '"';
                var graph = generateGraph(type, population.data, response.tvec.np_array, title);
                graph.options.xAxis.axisLabel = data.xlabel;
                graph.options.yAxis.axisLabel = data.ylabel;
                graphs.push(graph);
              });
            }
          });

          $scope.graphs = graphs;
        };


        $scope.runScenarios = function () {
          $http.post('/api/analysis/scenarios/run', $scope.runScenariosOptions)
            .success(function(data) {
              responseData = data;
              updateGraphs(responseData);
            });
        };


        $scope.openAddScenarioModal = function ($event) {
            if ($event) {
                $event.preventDefault();
            }

            return $modal.open({
                templateUrl: 'js/modules/analysis/analysis-scenarios-modal.html',
                controller: 'AnalysisScenariosModalController',
                resolve: {
                    scenario: function () {
                        return {};
                    },
                    availableScenarioParams: function() {
                      return availableScenarioParams;
                    },
                    populationNames: function() {
                      return meta.pops.long;
                    }
                }
            }).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    $scope.scenarios.push(newscenario);
                });
        };

        $scope.openEditScenarioModal = function ($event, scenario) {
            if ($event) {
                $event.preventDefault();
            }

            return $modal.open({
                templateUrl: 'js/modules/analysis/analysis-scenarios-modal.html',
                controller: 'AnalysisScenariosModalController',
                resolve: {
                    scenario: function () {
                      return scenario;
                    },
                    availableScenarioParams: function() {
                      return availableScenarioParams;
                    },
                    populationNames: function() {
                      return meta.pops.long;
                    }
                }
            }).result.then(
                function (newscenario) {
                    scenario.active = true;
                    _(scenario).extend(newscenario);
                });
        };

        $scope.onGraphTypeChange = function (type) {
          type.active = type.total || type.byPopulation;
          updateGraphs(responseData);
        };

        initialize();

    });

});
