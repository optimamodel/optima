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

    $scope.addDataToList = function(list, data, dataKey) {
      list.push(data);
      $scope.state[dataKey] = {};
    };

    $scope.deleteDataFromList = function(list, data) {
      var index = list.indexOf(data);
      list.splice(index, 1);
    };

    var fetchGraph = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progset/' + $scope.vm.selectedProgramSet.id + '/program/' +
        $scope.selectedProgram.id + '/costcoverage/graph?t=2015&parset_id=' + $scope.vm.selectedParset.id)
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
