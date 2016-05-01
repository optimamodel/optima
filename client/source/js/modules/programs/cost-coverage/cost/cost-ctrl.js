define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    $scope.state = {
      newCCData: {},
      newCPData: {},
      ccData: [],
      cpData: [],
      estdSize: []
    };
    $scope.Math = window.Math;

    $scope.selectedProgram = $scope.vm.programs[0];

    $scope.getProgramName = function(program) {
      if (program.name) {
        return program.name;
      } else {
        return program.short_name;
      }
    };

    $scope.changeSelectedProgram = function() {
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);
      $scope.state.chartData = [];
      fetchDefaultData();
      fetchEstimatedSize();
      $scope.updateGraph();
    };

    $scope.addToCCData = function(ccDataForm) {
      ccDataForm.spending.$setValidity("required", !angular.isUndefined($scope.state.newCCData.spending));
      ccDataForm.coverage.$setValidity("required", !angular.isUndefined($scope.state.newCCData.coverage));
      ccDataForm.year.$setValidity("valid", isValidCCDataYear());

      if(!ccDataForm.$invalid) {
        $http.put('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
          $scope.selectedProgram.id + '/costcoverage/data', $scope.state.newCCData)
          .success(function () {
            $scope.state.ccData.push($scope.state.newCCData);
            $scope.state.newCCData = {};
            $scope.state.showAddCCData = false;
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
      cpDataForm.splower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_lower));
      cpDataForm.spupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_upper));
      cpDataForm.uclower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_lower));
      cpDataForm.ucupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_upper));
      cpDataForm.year.$setValidity("valid", isValidCPDataYear());

      if(!cpDataForm.$invalid) {
        var newCPData = $scope.state.newCPData;
        var payload = {
          year: newCPData.year,
          unitcost_lower: newCPData.unitcost_lower,
          saturation_lower: newCPData.saturationpercent_lower/100.,
          unitcost_upper: newCPData.unitcost_upper,
          saturation_upper: newCPData.saturationpercent_lower/100.
        };
        console.log(newCPData);
        console.log(payload);
        $http.put(
            '/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
            $scope.selectedProgram.id + '/costcoverage/param',
            payload)
          .success(function () {
            $scope.state.cpData.push(newCPData);
            $scope.state.newCPData = {};
            $scope.state.showAddCPData = false;
            console.log(JSON.stringify($scope.state.cpData, null, 2));
          });
      }
    };

    var isValidCPDataYear = function() {
      if ($scope.state.newCPData.year) {
        if ($scope.state.newCPData.year >= $scope.vm.openProject.dataStart ||
          $scope.state.newCPData.year <= $scope.vm.openProject.dataEnd) {
          var recordExisting = _.filter($scope.state.cpData, function(cpData) {
            return cpData.year === $scope.state.newCPData.year;
          });
          if(recordExisting.length === 0) {
            return true;
          }
        }
      }
      return false;
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
      var years = _.map($scope.state.cpData, function(data) {
        return data.year;
      });

      if (years.length > 0) {
        var url = '/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
          $scope.selectedProgram.id + '/costcoverage/graph?t=' + years.join(',') + '&parset_id=' + $scope.vm.selectedParset.id;
        if ($scope.state.remarks) {
          $scope.state.displayCaption = angular.copy($scope.state.remarks);
          url += '&caption=' + encodeURIComponent($scope.state.remarks);
        }
        if ($scope.state.maxFunc) {
          url += '&xupperlim=' + $scope.state.maxFunc;
        }
        if ($scope.state.dispCost) {
          url += '&perperson=1'
        }
        $http.get(url)
          .success(function (response) {
            $scope.state.chartData = response;
          });
      }
    };

    var fetchEstimatedSize = function() {
      $http.get('/api/project/' + $scope.vm.openProject.id + '/progsets/' + $scope.vm.selectedProgramSet.id + '/programs/' +
        $scope.selectedProgram.id + '/costcoverage/popsize?t=2016&parset_id=' + $scope.vm.selectedParset.id)
        .success(function (response) {
          if(response.popsizes && response.popsizes.length > 0) {
            $scope.state.estdSize = {};
            response.popsizes.forEach(function(popSize){
              if(popSize.popsize) {
                $scope.state.estdSize[popSize.year] = Math.round(popSize.popsize);
              }
            });
          }
        });
    };

    function console_log_var(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    var fetchDefaultData = function() {
      $scope.state.ccData = [];
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);
      $scope.state.cpData = [];
      var ccopar = angular.copy($scope.selectedProgram.ccopars);
      if(ccopar && ccopar.t && ccopar.t.length > 0) {
        for(var index = 0;index < ccopar.t.length;index++) {
          $scope.state.cpData.push({
            year: ccopar.t[index],
            unitcost_lower: ccopar.unitcost[index][0],
            saturationpercent_lower: ccopar.saturation[index][0]*100.,
            unitcost_upper: ccopar.unitcost[index][1],
            saturationpercent_upper: ccopar.saturation[index][1]*100.
          })
        }
        $scope.updateGraph();
      }
    };

  });

});