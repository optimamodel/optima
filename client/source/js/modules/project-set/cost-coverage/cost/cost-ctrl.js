define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    var vc = $scope;
    $scope.state = {
      newCCData: {},
      newCPData: {},
      ccData: [],
      cpData: []
    };

    $scope.changeSelectedProgram = function() {
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);
      $scope.updateGraph();
      fetchDefaultData();
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

    $scope.addToCPData = function(cpDataForm) {
      $http.put('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage/param', $scope.state.newCPData)
        .success(function () {
          $scope.state.cpData.push($scope.state.newCPData);
          $scope.state.newCPData = {};
        });
    };

    $scope.removeFromCPData = function(data) {
      $http.delete('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage/param?year=' + data.year)
        .success(function () {
          var index = $scope.state.cpData.indexOf(data);
          $scope.state.cpData.splice(index, 1);
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
          if(response.data) {
            $scope.state.ccData = angular.copy(response.data);
          }
          if(response.params && response.params.t && response.params.t.length > 0) {
            for(var index = 0;index < response.params.t.length;index++) {
              $scope.state.cpData.push({
                year: response.params.t[index],
                unitcost_lower: response.params.unitcost[index][0],
                saturationpercent_lower: response.params.saturation[index][0],
                unitcost_upper: response.params.unitcost[index][1],
                saturationpercent_upper: response.params.saturation[index][1]
              })
            }
          }
        });
    };

  });

});