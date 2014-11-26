define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ModelViewController', function ($scope, $http, Model, f, meta) {

    var prepareF = function (f) {
      var F = angular.copy(f);

      F.dx = _(F.dx).map(parseFloat);
      F.force = _(F.force).map(parseFloat);
      F.init = _(F.init).map(parseFloat);
      F.tx1 = _(F.tx1).map(parseFloat);
      F.tx2 = _(F.tx2).map(parseFloat);
      return F;
    };

    var transformedF = prepareF(f[0]);

    $scope.parameters = {
      types: {
        force: 'Force-of-infection for ',
        init: 'Initial prevalence for ',
        dx: [
          'Testing rate initial value',
          'Testing rate final value',
          'Testing rate midpoint',
          'Testing rate slope'
        ],
        tx1: [
          'First-line ART initial value',
          'First-line ART final value',
          'First-line ART midpoint',
          'First-line ART slope'
        ],
        tx2: [
          'Second-line ART initial value',
          'Second-line ART final value',
          'Second-line ART midpoint',
          'Second-line ART slope'
        ]
      },
      meta: meta,
      f: transformedF,
      cache: {
        f: angular.copy(transformedF),
        response: null
      }
    };

    $scope.types = [
      { id: 'prev', name: 'Prevalence', active: true, byPopulation: true, total: false },
      { id: 'daly', name: 'DALYs per year', active: false, byPopulation: false, total: false },
      { id: 'death', name: 'HIV-related deaths per year', active: false, byPopulation: false, total: false },
      { id: 'inci', name: 'New HIV infections per year', active: false, byPopulation: false, total: false }
    ];

    var getActiveOptions = function () {
      return _($scope.types).where({ active: true });
    };

    $scope.enableManualCalibration = false;

    // to store years from UI
    $scope.simulationOptions = {};
    $scope.graphs = [];

    var linescatteroptions = {
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
        axisLabel: 'Prevalence (%)',
        tickFormat: function (d) {
          return d3.format(',.2f')(d);
        }
      }
    };

    var linescatterdata = {
      line: [],
      'scatter-error': []
  };

    $scope.doneEditingParameter = function () {
      console.log("I'm editing callback. Do what you have to do with me :(");
    };

    /*
     * Methods
     */

    var prepareGraphs = function (response) {
      var graphs = [], types;

      if (!response) {
        return graphs;
      }

      types = getActiveOptions();

      _(types).each(function (type) {
        var data = response[type.id];
        var scatterDataAvailable = data.pops.length === data.ydata.length;

        if (type.total) {
          var graph = {
            options: angular.copy(linescatteroptions),
            data: angular.copy(linescatterdata),
            type: type,
            title: 'Showing total data for "' + type.name + '"'
          };

          graph.data.line = _(data.tot).map(function (value, i) {
            //      x                 y
            return [response.tvec[i], value];
          });

          graph.options.xAxis.axisLabel = data.xlabel;
          graph.options.yAxis.axisLabel = data.ylabel;

          if (data.ydata.length === 1) {
            graph.data['scatter-error'] = _(data.ydata).chain()
            .map(function (value, i) {
              //      x                 y
              return [response.xdata[i], value];
            })
            .filter(function (value) {
              return !!value[1];
            })
            .value();
          }

          graphs.push(graph);
        }

        if (type.byPopulation) {
          _(data.pops).each(function (population, populationIndex) {
            var graph = {
              options: angular.copy(linescatteroptions),
              data: angular.copy(linescatterdata),
              type: type,
              title: 'Showing ' + type.name + ' for population "' + $scope.parameters.meta.pops.long[populationIndex] + '"'
            };

            graph.data.line = _(population.best).map(function (value, i) {
              //      x                 y
              return [response.tvec[i], value];
            });

            graph.options.xAxis.axisLabel = data.xlabel;
            graph.options.yAxis.axisLabel = data.ylabel;

            if (scatterDataAvailable) {
              graph.data['scatter-error'] = _(data.ydata[populationIndex]).chain()
                .map(function (value, i) {
                  //      x                 y
                  return [response.xdata[i], value];
                })
                .filter(function (value) {
                  return !!value[1];
                })
                .value();
            }

            graphs.push(graph);
          });
        }

      });

      return graphs;
    };

    var updateGraphs = function (data) {
      $scope.graphs = prepareGraphs(data);
      $scope.parameters.cache.response = data;
    };

    $scope.simulate = function () {
      $http.post('/api/model/view', $scope.simulationOptions)
        .success(updateGraphs);
    };

    $scope.previewManualCalibration = function () {
      Model.saveCalibrateManual({ F: prepareF($scope.parameters.f) }, updateGraphs);
    };

    $scope.saveManualCalibration = function () {
      Model.saveCalibrateManual({
        F: prepareF($scope.parameters.f),
        dosave: true
      }, updateGraphs);
    };

    $scope.revertManualCalibration = function () {
      angular.extend($scope.parameters.f, $scope.parameters.cache.f);
    };

    $scope.onGraphTypeChange = function (type) {
      type.active = type.total || type.byPopulation;
      updateGraphs($scope.parameters.cache.response);
    };

  });
});
