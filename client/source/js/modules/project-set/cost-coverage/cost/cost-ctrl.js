define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    var vc = $scope;
    $scope.state = {
      newAddData: {},
      ccData: []
    };

    $scope.changeSelectedProgram = function() {
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);
      fetchGraph();
    };

    $scope.addCCData = function() {
      $scope.state.ccData.push($scope.state.newAddData);
      $scope.state.newAddData = {};
    };

    var fetchGraph = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progset/' + $scope.vm.selectedProgramSet.id + '/program/' + $scope.selectedProgram.id + '/costcoverage/graph')
        .success(function (response) {
          console.log('response', response);
        });
    }
  });

});
