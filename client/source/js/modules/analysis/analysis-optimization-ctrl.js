define([
  './module'
], function (module) {
  'use strict';

  module.controller('AnalysisOptimizationController', function ($scope, $http, $interval) {
      
      $scope.params = {}
      $scope.params.objectives = {}
      $scope.params.objectives.what = 'outcome';

      $scope.pieoptions = {
          chart: {
              type: 'pieChart',
              height: 350,
              x: function(d){return d.key;},
              y: function(d){return d.y;},
              showLabels: false,
              transitionDuration: 500,
              labelThreshold: 0.01,
              legend: {
                  margin: {
                      top: 5,
                      right: 35,
                      bottom: 5,
                      left: 0
                  }
              }
          }
      };

      $scope.piedata1 = [
          {
              key: "Behavior change and communication",
              y: 34
          },
          {
              key: "Female sex workers",
              y: 6
          },
          {
              key: "Men who have sex with men",
              y: 1
          },
          {
              key: "People who inject drugs",
              y: 10
          },
          {
              key: "Sexually transmitted infections",
              y: 2
          },
          {
              key: "HIV counselling and testing",
              y: 6
          },
          {
              key: "Antiretroviral therapy",
              y: 44
          },
          {
              key: "Prevention of mother-to-child transmission",
              y: 6
          }
      ];

      $scope.piedata2 = [
          {
              key: "Behavior change and communication",
              y: 4
          },
          {
              key: "Female sex workers",
              y: 6
          },
          {
              key: "Men who have sex with men",
              y: 1
          },
          {
              key: "People who inject drugs",
              y: 20
          },
          {
              key: "Sexually transmitted infections",
              y: 2
          },
          {
              key: "HIV counselling and testing",
              y: 6
          },
          {
              key: "Antiretroviral therapy",
              y: 54
          },
          {
              key: "Prevention of mother-to-child transmission",
              y: 6
          }
      ];

      var timer;
      $scope.startOptimization = function () {
        $http.post('/api/optimization/start', $scope.params)
        .success(function (response) {
        })

        // Keep polling for data
        timer = $interval(function() {
          $http.get('/api/model/working')
          .success(function(data, status, headers, config) {
            if (data.status !== undefined && data.status == 'OK') {
              if ( angular.isDefined( timer ) ) {
                $interval.cancel(timer);
                timer = undefined;
              }
            } else {
              //updateGraphs(data);
            }
          })
          .error(function(data, status, headers, config) {
            if (angular.isDefined( timer )) {
              $interval.cancel(timer);
              timer = undefined;
            }
          });
        }, 5000, 0, false );
      };

      $scope.stopOptimization = function () {
        $http.get('/api/model/calibrate/stop')
        .success(function(data) {

        // Cancel timer
        if ( angular.isDefined( timer ) ) {
          $interval.cancel(timer);
          timer = undefined;
        }
      });

      $scope.saveOptimization = function () {
        $http.post('/api/model/calibrate/save')
        .success(function(data) {
        });
      };

      $scope.revertOptimization = function () {
        $http.post('/api/model/calibrate/revert')
        .success(function(data) {
        });
      };
    };
  });
});
