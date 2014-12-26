define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta, scenarioParamsResponse, CONFIG) {

        var linesGraphOptions, linesStyle, linesGraphData, responseData, availableScenarioParams;

        // initialize all necessary data for this controller
        var initialize = function() {

          // add All option in population list
          meta.pops.long.push("All");

          // transform scenarioParams to use attribute `names` instead of `keys`
          // it is the same for the data we have to send to run scenarios
          availableScenarioParams = _(scenarioParamsResponse.data.params).map(function(parameters) {
            return { name: parameters.name, names: parameters.keys, values: parameters.values};
          });

          $scope.scenarios = [
            {active: true, name: 'Conditions remain according to model calibration', pars: []}
          ];

          $scope.runScenariosOptions = {
            dosave: false
          };

          $scope.types = angular.copy(CONFIG.GRAPH_TYPES);

          $scope.lineStyles = ['__blue', '__green', '__red', '__orange',
            '__violet', '__black', '__light-orange', '__light-green'];

          linesGraphOptions = {
            height: 200,
            width: 320,
            margin: CONFIG.GRAPH_MARGINS,
            linesStyle: $scope.lineStyles,
            xAxis: {
              axisLabel: 'Year',
              tickFormat: function (d) {
                return d3.format('d')(d);
              }
            },
            yAxis: {
              axisLabel: ''
            }
          };

          linesGraphData = {
            lines: [],
            scatter: []
          };
        };

        /**
         * Returns an array containing arrays with [x, y] for d3 line data.
         */
        var generateLineData = function(xData, yData) {
          return _(yData).map(function (value, i) {
            return [xData[i], value];
          });
        };

        /**
         * Returns an graph based on the provided yData.
         *
         * yData should be an array where each entry contains an array of all
         * y-values from one line.
         */
        var generateGraph = function(yData, xData, title) {
          var graph = {
            options: angular.copy(linesGraphOptions),
            data: angular.copy(linesGraphData),
            title: title
          };

          _(yData).each(function(lineData) {
            graph.data.lines.push(generateLineData(xData, lineData));
          });

          return graph;
        };

        /**
         * Returns a financial graph.
         */
        var generateFinancialGraph = function(data) {
          var graph = generateGraph(data.data, data.xdata, data.title);

          graph.options.xAxis.axisLabel = data.xlabel;
          graph.options.yAxis.axisLabel = data.ylabel;
          graph.options.linesStyle = ['__black', '__black', '__black',
            '__black', '__black', '__black', '__black', '__black'];
          return graph;
        };

        /**
         * Regenerate graphs based on the response and type settings in the UI.
         */
        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }

          var graphs = [];

          _($scope.types.population).each(function (type) {

            var data = response[type.id];

            // generate graphs showing the overall data for this type
            if (type.total) {
              var title = data.tot.title;
              var graph = generateGraph(data.tot.data, response.tvec, title);
              graph.options.xAxis.axisLabel = data.xlabel;
              graph.options.yAxis.axisLabel = data.tot.ylabel;
              graph.legend = data.tot.legend;
              graphs.push(graph);
            }

            // generate graphs for this type for each population
            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {

                var title = population.title;
                var graph = generateGraph(population.data, response.tvec, title);
                graph.options.xAxis.axisLabel = data.xlabel;
                graph.options.yAxis.axisLabel = population.ylabel;
                graph.legend = population.legend;
                graphs.push(graph);
              });
            }
          });

          _($scope.types.financial).each(function (type) {
            // costcur = cost for current people living with HIV
            // costfut = cost for future people living with HIV
            // ann = annual costs
            // cum = cumulative costs
            if (type.annual) {
              var annualData = response[type.id].ann;
              graphs.push(generateFinancialGraph(annualData));
            }

            if (type.cumulative) {
              var cumulativeData = response[type.id].cum;
              graphs.push(generateFinancialGraph(cumulativeData));
            }
          });

          $scope.graphs = graphs;
        };

        /**
         * Returns a collection of entries where all non-active antries are filtered
         * out and the active attribute is removed from each of these entries.
         */
        var toCleanArray = function (collection) {
          return _(collection).chain()
          .where({ active: true })
          .map(function (item) {
            return _(item).omit(['active', '$$hashKey']);
          })
          .value();
        };


        $scope.runScenarios = function () {
          $scope.runScenariosOptions.scenarios = toCleanArray($scope.scenarios);
          $http.post('/api/analysis/scenarios/run', $scope.runScenariosOptions)
            .success(function(data) {
              responseData = data;
              updateGraphs(responseData);
            });
        };

        // Helper function to open a population modal
        var openScenarioModal = function(scenario) {
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
          });
        };

        $scope.openAddScenarioModal = function ($event) {
            if ($event) {
                $event.preventDefault();
            }

            var scenario = {};
            return openScenarioModal(scenario).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    newscenario.pars = newscenario.pars || [];
                    $scope.scenarios.push(newscenario);
                });
        };

        $scope.openEditScenarioModal = function ($event, scenario) {
            if ($event) {
                $event.preventDefault();
            }

            return openScenarioModal(scenario).result.then(
                function (newscenario) {
                    scenario.active = true;
                    _(scenario).extend(newscenario);
                });
        };

        // The graphs are shown/hidden after updating the graph type checkboxes.
        $scope.$watch('types', function () {
          updateGraphs(responseData);
        }, true);

        initialize();

    });

});
