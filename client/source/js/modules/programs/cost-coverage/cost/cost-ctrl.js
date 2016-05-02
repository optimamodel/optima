define(['./../../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller('CostController', function ($scope, $http) {

    $scope.state = {
      ccoparsTable: {},
      costcovTable: {},
      estdSize: []
    };

    // $scope.vm is from the controller of the cost-coverage template controller
    // that calls this template
    $scope.selectedProgram = $scope.vm.programs[0];

    function consoleLogVar(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    // $scope.Math = window.Math;

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
      $scope.state.chartData = [];
      var years = $scope.selectedProgram.ccopars.t;
      if (years.length == 0) {
        return;
      }
      var url = '/api/project/' + $scope.vm.openProject.id
          + '/progsets/' + $scope.vm.selectedProgramSet.id
          + '/programs/' + $scope.selectedProgram.id
          + '/costcoverage/graph?t=' + years.join(',')
          + '&parset_id=' + $scope.vm.selectedParset.id;
      if ($scope.state.remarks) {
        $scope.state.displayCaption = angular.copy($scope.state.remarks);
        url += '&caption=' + encodeURIComponent($scope.state.remarks);
      }
      if ($scope.state.maxFunc) {
        url += '&xupperlim=' + $scope.state.maxFunc;
      }
      if ($scope.state.dispCost) {
        url += '&perperson=1';
      }
      $http
        .get(url)
        .success(function (response) {
          $scope.state.chartData = response;
        });
    };

    var fetchEstimatedSize = function() {
      $scope.state.estdSize = {};
      $http
        .get(
          '/api/project/' + $scope.vm.openProject.id
            + '/progsets/' + $scope.vm.selectedProgramSet.id
            + '/program/' + $scope.selectedProgram.id
            + '/parset/' + $scope.vm.selectedParset.id
            + '/popsize')
        .success(function (response) {
          $scope.state.estdSize = response.popsizes;
          consoleLogVar('estdSize', $scope.state.estdSize);
        });
    };

    var saveSelectedProgram = function() {
      var payload = { 'program': $scope.selectedProgram };
      consoleLogVar("payload", payload);
      $http
        .post(
          '/api/project/' + $scope.vm.openProject.id
            + '/progsets/' + $scope.selectedProgram.progset_id
            + '/program',
          payload)
        .success(function() {
          $scope.updateGraph();
        });
    };

    var validateCostcovTable = function(table) {
      var costcov = [];
      table.rows.forEach(function(row, iRow, rows) {
        if (iRow != table.iEditRow) {
          costcov.push({year: row[0], cost: row[1], coverage: row[2]});
        }
      });
      $scope.selectedProgram.costcov = costcov;
      saveSelectedProgram();
    };

    var validateCcoparsTable = function(table) {
      var ccopars = {t: [], saturation: [], unitcost: []};
      table.rows.forEach(function(row, iRow, rows) {
        if (iRow != table.iEditRow) {
          ccopars.t.push(row[0]);
          ccopars.saturation.push([row[1]/100., row[2]/100.]);
          ccopars.unitcost.push([row[3], row[4]]);
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
      table.iEditRow = table.rows.length - 1;
    };

    $scope.deleteRow = function(table, iRow) {
      var iLastRow = table.rows.length - 1;
      table.rows.splice(iRow, 1);
      if (iLastRow == iRow) {
        $scope.addBlankRow(table);
      }
      table.iEditRow = table.rows.length - 1;
      table.validateFn(table);
    };

    $scope.editRow = function(table, iRow) {
      var iLastRow = table.rows.length - 1;
      if (table.iEditRow == iLastRow) {
        table.rows.splice(iLastRow, 1);
      }
      table.iEditRow = iRow;
      consoleLogVar("start_editing_table", table);
    };

    $scope.acceptEdit = function(table) {
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
        table.rows.push([val.year, val.cost, val.coverage]);
      });
      $scope.addBlankRow(table);
      consoleLogVar("costcovTable", $scope.state.costcovTable);

      $scope.state.ccoparsTable = {
        titles: [
          "Year", "Saturation % (low)", "Saturation % (High)",
          "Unitcost (low)", "Unitcost (high)"],
        rows: [],
        types: ["number", "number", "number", "number", "number"],
        widths: [],
        validateFn: validateCcoparsTable,
      };
      var ccopars = angular.copy($scope.selectedProgram.ccopars);
      var table = $scope.state.ccoparsTable;
      if (ccopars && ccopars.t && ccopars.t.length > 0) {
        for (var iYear = 0; iYear < ccopars.t.length; iYear++) {
          table.rows.push([
            ccopars.t[iYear],
            ccopars.saturation[iYear][0]*100.,
            ccopars.saturation[iYear][1]*100.,
            ccopars.unitcost[iYear][0],
            ccopars.unitcost[iYear][1]
          ])
        }
      }
      $scope.addBlankRow(table);
      consoleLogVar('ccoparsTable', $scope.state.ccoparsTable);
    };

    $scope.changeSelectedProgram = function() {
      buildTables();
      fetchEstimatedSize();
      $scope.updateGraph();
    };

    $scope.changeSelectedProgram()

  });

});