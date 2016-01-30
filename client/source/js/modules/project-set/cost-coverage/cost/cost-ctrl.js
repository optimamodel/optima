define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    var vc = $scope;
    $scope.newAddData = {};

    $scope.changeSelectedProgram = function() {
      $scope.ccData = angular.copy($scope.selectedProgram.addData);
      fetchGraph();
    };

    $scope.addCCData = function() {
      if (!$scope.ccData) {
        $scope.ccData = [];
      }
      $scope.ccData.push($scope.newAddData);
      $scope.newAddData = {};
    };


    var fetchGraph = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progset/' + $scope.vm.selectedProgramSet.id + '/program/' + $scope.selectedProgram.id + '/costcoverage/graph')
        .success(function (response) {
          console.log('response', response);
        });
    }
  });

});
