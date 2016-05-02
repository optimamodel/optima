define(['./../../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('CostController', function ($scope, $http) {

    $scope.state = {
      ccoparsTable: {},
      costcovTable: {},
      estdSize: []
    };
    $scope.Math = window.Math;
    $scope.selectedProgram = $scope.vm.programs[0];

    function console_log_var(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    $scope.getProgramName = function(program) {
      if (program.name) {
        return program.name;
      } else {
        return program.short;
      }
    };

    $scope.changeSelectedProgram = function() {
      $scope.state.chartData = [];
      buildTables();
      fetchEstimatedSize();
      $scope.updateGraph();
    };

      // ccDataForm.cost.$setValidity("required", !angular.isUndefined($scope.state.newCCData.cost));
      // ccDataForm.coverage.$setValidity("required", !angular.isUndefined($scope.state.newCCData.coverage));
      // ccDataForm.year.$setValidity("valid", isValidCCDataYear());

    // var isValidCCDataYear = function() {
    //   if ($scope.state.newCCData.year) {
    //     if ($scope.state.newCCData.year >= $scope.vm.openProject.dataStart ||
    //       $scope.state.newCCData.year <= $scope.vm.openProject.dataEnd) {
    //       var recordExisting = _.filter($scope.state.ccData, function(ccData) {
    //         return ccData.year === $scope.state.newCCData.year;
    //       });
    //       if(recordExisting.length === 0) {
    //         return true;
    //       }
    //     }
    //   }
    //   return false;
    // };


      // cpDataForm.splower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_lower));
      // cpDataForm.spupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_upper));
      // cpDataForm.uclower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_lower));
      // cpDataForm.ucupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_upper));
      // cpDataForm.year.$setValidity("valid", isValidCPDataYear());

    // var isValidCPDataYear = function() {
    //   if ($scope.state.newCPData.year) {
    //     if ($scope.state.newCPData.year >= $scope.vm.openProject.dataStart ||
    //       $scope.state.newCPData.year <= $scope.vm.openProject.dataEnd) {
    //       var recordExisting = _.filter($scope.state.cpData, function(cpData) {
    //         return cpData.year === $scope.state.newCPData.year;
    //       });
    //       if(recordExisting.length === 0) {
    //         return true;
    //       }
    //     }
    //   }
    //   return false;
    // };

    $scope.updateGraph = function() {
      var years = $scope.selectedProgram.ccopars.t;

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

    var saveSelectedProgram = function() {
      var projectId = $scope.vm.openProject.id;
      var progsetId = $scope.selectedProgram.progset_id;
      var payload = { 'program': $scope.selectedProgram };
      console_log_var("payload", payload);
      $http
          .post('/api/project/' + projectId + '/progsets/' + progsetId + '/program', payload)
          .success(function() {
            $scope.updateGraph();
          });
    };

    var validateCostcovTable = function(table) {
      var costcov = [];
      table.rows.forEach(function(row, i_row, rows) {
        if (i_row != table.i_edit_row) {
          costcov.push({year: row[0], cost: row[1], coverage: row[2]});
        }
      });
      $scope.selectedProgram.costcov = costcov;
      saveSelectedProgram();
    };

    var validateCcoparsTable = function(table) {
      var ccopars = {
        t: [],
        saturation: [],
        unitcost: []
      };
      table.rows.forEach(function(row, i_row, rows) {
        if (i_row != table.i_edit_row) {
          ccopars.t.push(row[0]),
          ccopars.saturation.push([row[1]/100., row[2]/100.]),
          ccopars.unitcost.push([row[3], row[4]])
        }
      });
      $scope.selectedProgram.ccopars = ccopars;
      saveSelectedProgram();
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
      validateCostcovTable(table);
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
      console_log_var('accept table', table)
      $scope.addBlankRow(table);
      table.validateFn(table);
    };

    var buildTables = function() {
      $scope.state.costcovTable = {
        titles: ["Year", "Cost", "Coverage"],
        rows: [],
        types: ["number", "number", "number"],
        widths: [],
        validateFn: validateCostcovTable,
      };
      var table = $scope.state.costcovTable;
      $scope.selectedProgram.costcov.forEach(function(val, i, list) {
        table.rows.push(
            [val.year, val.cost, val.coverage]);
      });
      $scope.addBlankRow(table);
      console_log_var("costcovTable", $scope.state.costcovTable);

      var ccopars = angular.copy($scope.selectedProgram.ccopars);

      $scope.state.ccoparsTable = {
        titles: ["Year", "Saturation % (low)", "Saturation % (High)", "Unitcost (low)", "Unitcost (high)"],
        rows: [],
        types: ["number", "number", "number", "number", "number"],
        widths: [],
        validateFn: validateCcoparsTable,
      };
      var table = $scope.state.ccoparsTable;
      if (ccopars && ccopars.t && ccopars.t.length > 0) {
        for (var i_year = 0; i_year < ccopars.t.length; i_year++) {
          table.rows.push([
            ccopars.t[i_year],
            ccopars.saturation[i_year][0]*100.,
            ccopars.saturation[i_year][1]*100.,
            ccopars.unitcost[i_year][0],
            ccopars.unitcost[i_year][1],
          ])
        }
        $scope.updateGraph();
      }
      $scope.addBlankRow(table);
      console_log_var('ccoparsTable', $scope.state.ccoparsTable);
    };

    $scope.changeSelectedProgram()

  });

});