define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';
    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta, info, scenarioParametersResponse, progsetsResponse, parsetResponse, scenariosResponse, CONFIG, typeSelector, $state) {
        // In case there is no model data the controller only needs to show the
        // warning that the user should upload a spreadsheet with data.
        var openProject  = info.data;
        if (!openProject.has_data) {
          $scope.missingModelData = true;
          return;
        }

        var responseData, availableScenarioParameters, availableScenarios;
        $scope.scenarios = scenariosResponse.data.scenarios;
        $scope.progsets = progsetsResponse.data.progsets;
        $scope.parsets = parsetResponse.data.parsets;

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
          $http.put('/api/project/'+openProject.id+'/scenarios', {
            'scenarios': $scope.scenarios
          }).success(function(response) {
            $scope.scenarios = response.scenarios;
          });
        };

        // Helper function to open a population modal
        var openScenarioModal = function(scenario) {
          return $modal.open({
            templateUrl: 'js/modules/parameter-scenarios-modal/parameter-scenarios-modal.html',
            controller: 'ParameterScenariosModalController',
            resolve: {
              scenario: function () {
                return scenario;
              },
              parsets: function() {
                return $http.get('/api/project/' + openProject.id + '/parsets');
              },
              openProject: function(){
                return openProject;
              }
            }
          });
        };

        $scope.openScenarioModal = function (row, action, $event) {
            if ($event) { $event.preventDefault(); }

            if(action === 'add'){
              return openScenarioModal(row).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    newscenario.pars = newscenario.pars || [];
                    $scope.scenarios.push(newscenario);
                });
            }else if(action === 'edit'){
              return openScenarioModal(row).result.then(
                function (updatescenario) {
                    console.log('Updated ', updatescenario);
                });
            }else if(action === 'copy'){
              var newscenario = angular.copy(row);
              newscenario.name = row.name +' Copy'
              $scope.scenarios.push(newscenario);
            }else if(action === 'delete'){
              $scope.scenarios = _.without($scope.scenarios, _.findWhere($scope.scenarios, {name: row.name}));
            }
            /*return openScenarioModal(scenario).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    newscenario.pars = newscenario.pars || [];
                    $scope.scenarios.push(newscenario);
                });*/
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

        $scope.progset_name = function(progset_id) {
          var progset = _.filter($scope.progsets, {id: progset_id});
          if (progset.length > 0) {
            return progset[0].name;
          }
          return '';
        }


        $scope.parset_name = function(parset_id) {
          var parset = _.filter($scope.parsets, {id: parset_id});
          if (parset.length > 0) {
            return parset[0].name;
          }
          return '';
        }
    });

});
