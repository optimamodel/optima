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
      fetchDefaultData();
    };

    $scope.addCCData = function() {
      $scope.state.ccData.push($scope.state.newAddData);
      $scope.state.newAddData = {};
    };

    $scope.deleteCCData = function(data) {
      var index = $scope.state.ccData.indexOf(data);
      $scope.state.ccData.splice(index, 1);
    };

    var fetchGraph = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progset/' + $scope.vm.selectedProgramSet.id + '/program/' + $scope.selectedProgram.id + '/costcoverage/graph')
        .success(function (response) {
          console.log('response', response);
        });
    };

    var fetchDefaultData = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progset/' + $scope.vm.selectedProgramSet.id + '/program/' + $scope.selectedProgram.id + '/costcoverage')
        .success(function (response) {
          console.log('response', response);
        });
    }

  });

});
