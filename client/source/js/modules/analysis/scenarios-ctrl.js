define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';
    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta, info, scenarioParametersResponse, scenariosResponse, CONFIG, typeSelector, $state) {
        // In case there is no model data the controller only needs to show the
        // warning that the user should upload a spreadsheet with data.
        var openProject  = info.data;
        if (!openProject.has_data) {
          $scope.missingModelData = true;
          return;
        }

        var responseData, availableScenarioParameters, availableScenarios;
        $scope.scenarios = scenariosResponse.data.scenarios;

        /*$scope.runScenariosOptions = {
          dosave: false
        };

        $scope.saveScenariosOptions = {
          dosave: false
        };*/
        // initialize all necessary data for this controller
        var initialize = function() {
          $scope.scenarios = [];

          

          // add All option in population list
          //meta.data.pops.long.push("All");

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

          $scope.types = typeSelector.types;
        };

        /**
         * Returns an graph based on the provided yData.
         *
         * yData should be an array where each entry contains an array of all
         * y-values from one line.
         */
        var generateGraph = function(yData, xData, title, legend, xLabel,  yLabel) {
          var graph = {
            options: {
              height: 200,
              width: 320,
              margin: CONFIG.GRAPH_MARGINS,
              xAxis: {
                axisLabel: 'Year'
              },
              yAxis: {
                axisLabel: ''
              },
              areasOpacity: 0.1
            },
            data: {
              lines: [],
              scatter: [],
              areas: []
            },
            title: title
          };

          graph.options.xAxis.axisLabel = xLabel;
          graph.options.yAxis.axisLabel = yLabel;
          graph.options.legend = legend;
          graph.options.title = title;

          // scenario chart data like prevalence have `best` & `data`
          // financial chart data only has one property `data`
          var linesData = yData.best || yData.data;
          _(linesData).each(function(lineData) {
            graph.data.lines.push(_.zip(xData, lineData));
          });

          // the scenario charts have an uncertenty area `low` & `high`
          if (!_.isEmpty(yData.low) && !_.isEmpty(yData.high)) {
            _(yData.high).each(function(highLineData, index) {
              graph.data.areas.push({
                highLine: _.zip(xData, highLineData),
                lowLine: _.zip(xData, yData.low[index])
              });
            });
          }

          return graph;
        };

        /**
         * Returns a financial graph.
         */
        var generateFinancialGraph = function (data) {
          var graph = generateGraph(data, data.xdata, data.title, data.legend, data.xlabel, data.ylabel);
          return graph;
        };

        /**
         * Regenerate graphs based on the response and type settings in the UI.
         */
        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }
          typeSelector.enableAnnualCostOptions($scope.types, response);

          var graphs = [];

          _($scope.types.population).each(function (type) {

            var data = response[type.id];

            // generate graphs showing the overall data for this type
            if (type.total) {
              var title = data.tot.title;
              var graph = generateGraph(data.tot, response.tvec, title, data.tot.legend, data.xlabel, data.tot.ylabel);
              graphs.push(graph);
            }

            // generate graphs for this type for each population
            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {

                var title = population.title;
                var graph = generateGraph(population, response.tvec, title, population.legend, data.xlabel, population.ylabel);
                graphs.push(graph);
              });
            }
          });

          // annual cost charts
          _($scope.types.possibleKeys).each(function(type) {
            var isActive = $scope.types.costs.costann[type];
            if (isActive) {
              var chartData = response.costann[type][$scope.types.activeAnnualCost];
              if (chartData) {
              graphs.push(generateFinancialGraph(chartData));
              }
            }
          });


          // cumulative cost charts
          _($scope.types.possibleKeys).each(function(type) {
            var isActive = $scope.types.costs.costcum[type];
            if (isActive) {
              var chartData = response.costcum[type];
              if (chartData) {
                graphs.push(generateFinancialGraph(chartData));
              }
            }
          });

          // commitments

          var commitIsActive = $scope.types.costs.costann.checked;
          if (commitChartData && commitIsActive) {
            var commitChartData = response.commit[$scope.types.activeAnnualCost];
            if (commitChartData) {
              graphs.push(generateFinancialGraph(commitChartData));
            }
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
          //$scope.runScenariosOptions.scenarios = toCleanArray($scope.scenarios);
          //$scope.runScenariosOptions.dosave = saveScenario === true;
          var activeScenarios = _.filter($scope.scenarios, function(scenario){ return scenario.active; });
          $http.get('/api/project/'+openProject.id+'/scenarios/results')
            .success(function(data) {
              responseData = data;
              updateGraphs(responseData);
            });
        };

        $scope.saveScenarios = function (saveScenario) {
          angular.forEach($scope.scenarios, function(sc){
            console.log(sc);
            $http.post('/api/project/'+openProject.id+'/scenarios?name='+sc.name+'&parset_id='+sc.parset_id+'&scenario_type='+sc.scenario_type+'&active='+sc.active+'', { pars: sc.pars })
              .success(function(response) {
                console.log(response);
              });
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
                return meta.data.pops.long;
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
          $state.go('model');;
        };

        // The graphs are shown/hidden after updating the graph type checkboxes.
        $scope.$watch('types', function () {
          updateGraphs(responseData);
        }, true);

        //initialize();

    });

});
