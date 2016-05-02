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

    var validate_fn = function(table) {
      var addData = [];
      table.rows.forEach(function(row, i_row, rows) {
        if (i_row != table.i_edit_row) {
          addData.push({year: row[0], spending: row[1], coverage: row[2]});
        }
      });
      var program = angular.copy($scope.selectedProgram);
      program.addData = addData;
      var projectId = $scope.vm.openProject.id;
      var progsetId = program.progset_id;
      var payload = { 'program': program };
      $http.post('/api/project/' + projectId + '/progsets/' + progsetId + '/program', payload);
      console_log_var("payload", payload);
    };

    $scope.addBlankRow = function(table) {
      var n_var = table.titles.length;
      var row = [];
      for (var j=0; j<n_var; j+=1) {
        row.push("");
      }
      table.rows.push(row);
      table.i_edit_row = table.rows.length - 1;
    };

    $scope.deleteRow = function(table, i_row) {
      var i_last_row = table.rows.length - 1;
      table.rows.splice(i_row, 1);
      if (i_last_row == i_row) {
        $scope.addBlankRow(table);
      }
      table.i_edit_row = table.rows.length - 1;
      validate_fn(table);
      console_log_var("table", table);
    }

    $scope.editRow = function(table, i) {
      var i_last_row = table.rows.length - 1;
      if (table.i_edit_row == i_last_row) {
        table.rows.splice(i_last_row, 1);
      }
      table.i_edit_row = i;
      console_log_var("table", table);
    }

    $scope.acceptEdit = function(table) {
      $scope.addBlankRow(table);
      table.validate_fn(table);
    };

    var fetchDefaultData = function() {
      $scope.state.ccData = [];
      $scope.state.ccData = angular.copy($scope.selectedProgram.addData);

      $scope.state.costCovDataTable = {
        titles: ["Year", "Spending", "Coverage"],
        rows: [],
        types: ["number", "number", "number"],
        widths: [],
        validate_fn: validate_fn,
      };
      var table = $scope.state.costCovDataTable;
      $scope.selectedProgram.addData.forEach(function(val, i, list) {
        table.rows.push(
            [val.year, val.spending, val.coverage]);
      });
      $scope.addBlankRow(table);
      console_log_var("table", table);

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



    $scope.changeSelectedProgram()

  });

});