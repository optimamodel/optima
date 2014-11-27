define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta) {

        $scope.projectParams = {
            name: ''
        };

        $scope.scenarios = [
            { name: 'Conditions remain according to model calibration', active: true }
        ];

        $scope.types = [
          { id: 'prev', name: 'Prevalence', active: true, byPopulation: true, total: false },
          { id: 'daly', name: 'DALYs', active: false, byPopulation: false, total: false },
          { id: 'death', name: 'Deaths', active: false, byPopulation: false, total: false },
          { id: 'inci', name: 'New infections', active: false, byPopulation: false, total: false },
          { id: 'dx', name: 'Diagnoses', active: false, byPopulation: false, total: false },
          { id: 'tx1', name: 'First-line treatment', active: false, byPopulation: false, total: false },
          { id: 'tx2', name: 'Second-line treatment', active: false, byPopulation: false, total: false }
        ];

        $scope.runScenariosOptions = {};

        var linesGraphOptions = {
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
            axisLabel: 'lala',
            tickFormat: function (d) {
              return d3.format(',.2f')(d);
            }
          }
        };

        var linesGraphData = {
          lines: [],
          scatter: []
        };

        var cashedData;

        /*
        * Returns an array containing arrays with [x, y] for d3 line data.
        */
        var generateLineData = function(xData, yData) {
          return _(yData).map(function (value, i) {
            return [xData[i], value];
          });
        };

        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }

          var graphs = [];

          _($scope.types).each(function (type) {

            var data = response[type.id];

            if (type.total) {
              var graph = {
                options: angular.copy(linesGraphOptions),
                data: angular.copy(linesGraphData),
                type: type,
                title: 'Showing total data for "' + type.name + '"'
              };

              _(data.tot.data).each(function(lineData) {
                graph.data.lines.push(generateLineData(response.tvec.np_array, lineData));
              });

              graph.options.xAxis.axisLabel = data.xlabel;
              graph.options.yAxis.axisLabel = data.ylabel;

              graphs.push(graph);

            }

            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {
                var graph = {
                  options: angular.copy(linesGraphOptions),
                  data: angular.copy(linesGraphData),
                  type: type,
                  title: 'Showing ' + type.name + ' for population "' + meta.pops.long[populationIndex] + '"'
                };

                _(population.data).each(function(lineData) {
                  graph.data.lines.push(generateLineData(response.tvec.np_array, lineData));
                });

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
              cashedData = data;
              updateGraphs(cashedData);
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
                        return {
                            sex: 'male'
                        };
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
                    }
                }
            }).result.then(
                function (newscenario) {
                    scenario.active = true;
                    _(scenario).extend(newscenario);
                });
        };



        var toCleanArray = function (collection) {
            return _(collection).chain()
                .where({ active: true })
                .map(function (item) {
                    return _(item).omit(['active', '$$hashKey']);
                })
                .value();
        };

        $scope.onGraphTypeChange = function (type) {
          type.active = type.total || type.byPopulation;
          updateGraphs(cashedData);
        };

    });

});
