define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    var vc = $scope;
    $scope.state = {
      newCCData: {},
      newCPData: {},
      ccData: [],
      ccDataSaved: []
    };

    $scope.changeSelectedProgram = function() {
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);
      $scope.updateGraph();
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

    $scope.addToCCData = function(ccDataForm) {
      ccDataForm.spending.$setValidity("required", !angular.isUndefined($scope.state.newCCData.spending));
      ccDataForm.coverage.$setValidity("required", !angular.isUndefined($scope.state.newCCData.coverage));
      ccDataForm.year.$setValidity("valid", isValidCCDataYear());

      if($scope.state.newCCData.year && $scope.state.newCCData.spending >= 0 && $scope.state.newCCData.coverage >= 0) {
        $http.put('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
          $scope.selectedProgram.id + '/costcoverage/data', $scope.state.newCCData)
          .success(function () {
            $scope.state.ccData.push($scope.state.newCCData);
            $scope.state.newCCData = {};
          });
      }
    };

    var isValidCCDataYear = function() {
      if ($scope.state.newCCData.year) {
        if ($scope.state.newCCData.year >= $scope.vm.openProject.dataStart ||
          $scope.state.newCCData.year <= $scope.vm.openProject.dataEnd) {
          var recordExisting = _.filter($scope.state.ccData, function(ccData) {
            return ccData.year === $scope.state.newCCData.year;
          });
          if(recordExisting.length === 0) {
            return true;
          }
        }
      }
      return false;
    };

    $scope.removeFromCCData = function(data) {
      $http.delete('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage/data?year=' + data.year)
        .success(function () {
          var index = $scope.state.ccData.indexOf(data);
          $scope.state.ccData.splice(index, 1);
        });
    };

    $scope.updateGraph = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage/graph?t=2016&parset_id=' + $scope.vm.selectedParset.id)
        .success(function (response) {
          $scope.state.chartData = response;
        });
    };

    var fetchDefaultData = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage')
        .success(function (response) {
          $scope.state.ccDataSaved = angular.copy(response.data);
          setCCData();
        });
    };

    var setCCData = function() {
      $scope.state.ccData = $scope.state.ccDataSaved;
    };

    $scope.reset = function() {
      setCCData();
      $scope.state.remarks = '';
      $scope.state.maxFunc = undefined;
      $scope.state.dispCost = undefined;
    }
  });

});
