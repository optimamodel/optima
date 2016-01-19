define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramModalController', function ($scope, $modalInstance, program, populations, programList, modalService, parameters, categories) {

    // Default list of criteria
    var hivstatus = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids', 'allstates'];

    // Initializes controller state and sets some default values in the program
    var initialize = function () {

      $scope.state = {
        selectAll: false,
        isNew: !program.name,
        populations: angular.copy(populations),
        parameters: parameters,
        categories: categories,
        program: program,
        eligibility: {
          pregnantFalse: true,
          allstates: true
        },
        showAddData: false
      };

      // todo: remove later
      program.addData = [{
        year: 2026,
        spending: 500000,
        coverage: 10000
      }];

      if(program.populations && program.populations.length > 0) {
        _.forEach($scope.state.populations, function(population) {
          population.active = (program.populations.length==0) || (program.populations.indexOf(population.short_name) > -1);
        });
        $scope.state.selectAll = !_.find($scope.state.populations, function(population) {
          return !population.active;
        })
      }

      _.forEach($scope.state.program.parameters, function(parameter) {
        parameter.parameterObj = _.find(parameters, function(param) {
          return parameter.param === param.short;
        });
      });

      $scope.state.program.active = true;
      if ($scope.state.isNew) {
        $scope.state.program.category = 'Other';
      }

      if($scope.state.program.criteria) {
        $scope.state.eligibility.pregnantFalse = !$scope.state.program.criteria.pregnant;
        if($scope.state.program.criteria.hivstatus && $scope.state.program.criteria.hivstatus.length > 0
          && $scope.state.program.criteria.hivstatus !== 'allstates') {
          _.each($scope.state.program.criteria.hivstatus, function(state) {
            $scope.state.eligibility[state] = true;
          });
          $scope.state.eligibility.allstates = false;
        }
      } else {
        $scope.state.program.criteria = {}
      }
    };

    // Function to set eligibility selection
    $scope.setEligibility = function(selectedEligibility) {
      if(selectedEligibility === 'allstates') {
        $scope.state.eligibility.acute = false;
        $scope.state.eligibility.gt500 = false;
        $scope.state.eligibility.gt350 = false;
        $scope.state.eligibility.gt200 = false;
        $scope.state.eligibility.gt50 = false;
        $scope.state.eligibility.aids = false;
      } else {
        $scope.state.eligibility.allstates = false;
      }
    };

    // Function to select all populations
    $scope.selectAllPopulations = function() {
      _.forEach($scope.state.populations, function(population) {
        population.active = $scope.state.selectAll;
      });
    };

    // Function to select or un-select SelectAll when other populations are selected
    $scope.setSelectAll = function() {
      $scope.state.selectAll = true;
      _.forEach($scope.state.populations, function(population) {
        if(!population.active) {
          $scope.state.selectAll = false;
        }
      });
    };

    // Function to check if program name is unique
    $scope.isUniqueName = function (name, programForm) {
      var exists = _(programList).some(function(program) {
        return program.name == name && program.id !== $scope.state.program.id;
      });
      programForm.programName.$setValidity("programExists", !exists);
      return exists;
    };

    // Function to add a new parameter
    $scope.addParameter = function () {
      $scope.state.program.parameters = $scope.state.program.parameters || [];
      $scope.state.program.parameters.push({active: true});
    };

    // Function to remove a parameter
    $scope.removeParameter = function ($index) {
      program.parameters.splice($index,1);
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined,'Please fill in the form correctly');
      } else {

        $scope.state.showAddData = false;

        $scope.state.program.populations = _.filter($scope.state.populations, function(population) {
          return population.active;
        }).map(function(population) {
          return population.short_name;
        });

        $scope.state.program.criteria.hivstatus = _.filter(hivstatus, function(state) {
          return $scope.state.eligibility[state];
        }).map(function(state) {
          return state;
        });

        _.forEach($scope.state.program.parameters, function(parameter) {
          parameter.param = parameter.parameterObj.short;
          delete parameter.parameterObj;
        });

        console.log('$scope.state.program', $scope.state.program);

        $modalInstance.close($scope.state.program);
      }
    };

    initialize();

  });

});
