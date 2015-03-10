define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, $window, meta, info, scenarioParametersResponse, scenariosResponse, CONFIG, graphTypeFactory) {

        var linesGraphOptions, linesGraphData, responseData, availableScenarioParameters, availableScenarios;

        // initialize all necessary data for this controller
        var initialize = function() {
          $scope.validate = false;
          $scope.show_message = false;
          $scope.scenarios = [];

          $scope.runScenariosOptions = {
            dosave: false
          };

          // check if project is calibrated
          checkProjectInfo(info);

          if($scope.validate) {
            // add All option in population list
            meta.pops.long.push("All");

            // transform scenarioParameters to use attribute `names` instead of `keys`
            // it is the same for the data we have to send to run scenarios
            availableScenarioParameters = _(scenarioParametersResponse.data.parameters).map(function(parameters) {
              return { name: parameters.name, names: parameters.keys, values: parameters.values};
            });

            availableScenarios = scenariosResponse.data.scenarios;

            $scope.scenarios = _(availableScenarios).map(function(scenario) {
              scenario.active = true;
              return scenario;
            });
          }

          $scope.types = graphTypeFactory.types;
          // reset graph types every time you come to this page
          angular.extend($scope.types, angular.copy(CONFIG.GRAPH_TYPES));

          linesGraphOptions = {
            height: 200,
            width: 320,
            margin: CONFIG.GRAPH_MARGINS,
            xAxis: {
              axisLabel: 'Year'
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

        var checkProjectInfo = function (info) {
          if (!info) return;
          var data = info.data;
          if ( data.status == "OK" ) {
            $scope.validate = data.can_scenarios;
            $scope.show_message = !$scope.validate;
          }
        };

        /**
         * Returns an graph based on the provided yData.
         *
         * yData should be an array where each entry contains an array of all
         * y-values from one line.
         */
        var generateGraph = function(yData, xData, title, legend, xLabel,  yLabel) {
          var graph = {
            options: angular.copy(linesGraphOptions),
            data: angular.copy(linesGraphData),
            title: title
          };

          graph.options.xAxis.axisLabel = xLabel;
          graph.options.yAxis.axisLabel = yLabel;
          graph.options.legend = legend;
          graph.options.title = title;

          _(yData).each(function(lineData) {
            graph.data.lines.push(_.zip(xData, lineData));
          });

          return graph;
        };

        /**
         * Returns a financial graph.
         */
        var generateFinancialGraph = function (data) {
          var graph = generateGraph(data.data, data.xdata, data.title, data.legend, data.xlabel, data.ylabel);
          return graph;
        };

        /**
         * Regenerate graphs based on the response and type settings in the UI.
         */
        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }
          graphTypeFactory.enableAnnualCostOptions($scope.types, response);

          var graphs = [];

          _($scope.types.population).each(function (type) {

            var data = response[type.id];

            // generate graphs showing the overall data for this type
            if (type.total) {
              var title = data.tot.title;
              var graph = generateGraph(data.tot.data, response.tvec, title, data.tot.legend, data.xlabel, data.tot.ylabel);
              graphs.push(graph);
            }

            // generate graphs for this type for each population
            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {

                var title = population.title;
                var graph = generateGraph(population.data, response.tvec, title, population.legend, data.xlabel, population.ylabel);
                graphs.push(graph);
              });
            }
          });

          // annual cost charts
          _(['existing', 'future', 'total']).each(function(type) {
            var chartData = response.costann[type][$scope.types.activeAnnualCost];
            var isActive = $scope.types.costs[0][type];
            if (chartData && isActive) {
              graphs.push(generateFinancialGraph(chartData));
            }
          });


          // cumulative cost charts
          _(['existing', 'future', 'total']).each(function(type) {
            var chartData = response.costcum[type];
            var isActive = $scope.types.costs[1][type];
            if (chartData && isActive) {
              graphs.push(generateFinancialGraph(chartData));
            }
          });

          // commitments
          var commitChartData = response.commit[$scope.types.activeAnnualCost];
          var commitIsActive = $scope.types.costs[2].checked;
          if (commitChartData && commitIsActive) {
            graphs.push(generateFinancialGraph(commitChartData));
          }

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

        $scope.runScenarios = function (saveScenario) {
          $scope.runScenariosOptions.scenarios = toCleanArray($scope.scenarios);
          $scope.runScenariosOptions.dosave = saveScenario === true;
          $http.post('/api/analysis/scenarios/run', $scope.runScenariosOptions)
            .success(function(data) {
              responseData = data;
              updateGraphs(responseData);
            });
        };

        // Helper function to open a population modal
        var openScenarioModal = function(scenario) {
          return $modal.open({
            templateUrl: 'js/modules/analysis/scenarios-modal.html',
            controller: 'AnalysisScenariosModalController',
            resolve: {
              scenario: function () {
                return scenario;
              },
              availableScenarioParameters: function() {
                return availableScenarioParameters;
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

        $scope.gotoViewCalibrate = function() {
          $window.location.href = '#/model/view';
        };

        // The graphs are shown/hidden after updating the graph type checkboxes.
        $scope.$watch('types', function () {
          updateGraphs(responseData);
        }, true);

        initialize();

    });

});
