define(['./../../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller('CostController', function ($scope, $http) {

    // $scope.vm is from the cost-coverage template controller
    $scope.selectedProgram = $scope.vm.programs[0];

    var initialize = function() {
      $scope.changeSelectedProgram()
    };

    $scope.changeSelectedProgram = function() {
      buildTables();
      $scope.updateGraph();
      $scope.popsizes = {};
      $http
        .get(
          '/api/project/' + $scope.vm.openProject.id
            + '/progsets/' + $scope.vm.selectedProgramSet.id
            + '/program/' + $scope.selectedProgram.id
            + '/parset/' + $scope.vm.selectedParset.id
            + '/popsizes')
        .success(function (response) {
          $scope.popsizes = response;
        });
    };

    function consoleLogVar(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    $scope.updateGraph = function() {
      $scope.chartData = [];
      var years = $scope.selectedProgram.ccopars.t;
      if (years.length == 0) {
        return;
      }
      var url = '/api/project/' + $scope.vm.openProject.id
          + '/progsets/' + $scope.vm.selectedProgramSet.id
          + '/programs/' + $scope.selectedProgram.id
          + '/costcoverage/graph?t=' + years.join(',')
          + '&parset_id=' + $scope.vm.selectedParset.id;
      if ($scope.remarks) {
        $scope.displayCaption = angular.copy($scope.remarks);
        url += '&caption=' + encodeURIComponent($scope.remarks);
      }
      if ($scope.maxFunc) {
        url += '&xupperlim=' + $scope.maxFunc;
      }
      if ($scope.dispCost) {
        url += '&perperson=1';
      }
      $http
        .get(url)
        .success(function (response) {
          $scope.chartData = response;
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

    var showEstPopFn = function(row) {
      var year = row[0];
      if (!_.isNumber(parseInt(year)))
          return "";
      var popsize = $scope.popsizes[year.toString()];
      if (!_.isNumber(popsize))
          return "";
      return parseInt(popsize);
    };

    var buildTables = function() {
      $scope.costcovTable = {
        titles: ["Year", "Cost", "Coverage"],
        rows: [],
        types: ["number", "number", "number"],
        widths: [],
        displayRowFns: [],
        validateFn: validateCostcovTable,
      };
      var table = $scope.costcovTable;
      $scope.selectedProgram.costcov.forEach(function(val, i, list) {
        table.rows.push([val.year, val.cost, val.coverage]);
      });
      consoleLogVar("costcovTable", $scope.costcovTable);

      $scope.ccoparsTable = {
        titles: [
          "Year", "Population", "Saturation % (low)", "Saturation % (High)",
          "Unitcost (low)", "Unitcost (high)"],
        rows: [],
        types: ["number", "displayFn", "number", "number", "number", "number"],
        widths: [],
        displayRowFns: [null, showEstPopFn, null, null, null, null],
        validateFn: validateCcoparsTable,
      };
      var ccopars = angular.copy($scope.selectedProgram.ccopars);
      var table = $scope.ccoparsTable;
      if (ccopars && ccopars.t && ccopars.t.length > 0) {
        for (var iYear = 0; iYear < ccopars.t.length; iYear++) {
          table.rows.push([
            ccopars.t[iYear],
            "",
            ccopars.saturation[iYear][0]*100.,
            ccopars.saturation[iYear][1]*100.,
            ccopars.unitcost[iYear][0],
            ccopars.unitcost[iYear][1]
          ])
        }
      }
      consoleLogVar('ccoparsTable', $scope.ccoparsTable);
    };

    initialize();

  });

});


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

