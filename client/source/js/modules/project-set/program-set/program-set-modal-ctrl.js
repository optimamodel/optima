define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetModalController', function ($scope, $modalInstance, program, populations, programList, modalService, parameters, categories) {

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
        }
      };

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
        if(parameter.parameterObj && parameter.parameterObj.pships && parameter.parameterObj.pships.length > 0) {
          _.forEach(parameter.parameterObj.pships, function(pship) {
            _.forEach(parameter.pops, function(pop) {
              if(angular.equals(pship, pop)) {
                pship.added = true;
              }
            });
          });
          parameter.selectAll = parameter.parameterObj.pships && parameter.pops && parameter.parameterObj.pships.length === parameter.pops.length;
        } else {
          var selectedPopulation = _.map(parameter.pops, function(pop) {
            return _.find($scope.state.populations, function(populations) {
              return pop === populations.short_name;
            });
          });
          parameter.populations = angular.copy(selectedPopulation);
          _.forEach(parameter.populations, function(population) {
            population.added = true;
          });
          parameter.populations = _.extend(angular.copy($scope.state.populations), parameter.populations);
          parameter.selectAll = parameter.populations && $scope.state.populations && parameter.populations.length === $scope.state.populations.length;
        }
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

    // Add a new parameter
    $scope.addParameter = function() {
      $scope.state.program.parameters.push({active: true});
    };

    $scope.addPopulations = function(parameter) {
      if(!parameter.pships || parameter.pships.length === 0) {
        parameter.populations = $scope.state.populations;
      }
    };

    // Function to add/remove all populations to a parameter
    $scope.addRemoveAllPopToParameter = function(param) {
      _.forEach(param.populations, function(population) {
        population.added = param.selectAll;
      });
    };

    // Function to add/remove all partnerships to a parameter
    $scope.addRemoveAllPshipsToParameter = function(param) {
      _.forEach(param.parameterObj.pships, function(pship) {
        pship.added = param.selectAll;
      });
    };

    // Function to remove a parameter
    $scope.removeParameter = function ($index) {
      program.parameters.splice($index,1);
    };

    // Submit form for saving program and closing modal
    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined,'Please fill in the form correctly');
      } else {

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
          var addedPopulations = _.filter(parameter.populations, function(population){
            return population.added;
          });
          if(addedPopulations && addedPopulations.length > 0) {
            parameter.pops = addedPopulations.map(function (population) {
              return population.short_name;
            });
          }
          var selectedPartnerships = _.filter(parameter.parameterObj.pships, function(pship){
            return pship.added;
          });
          if(selectedPartnerships && selectedPartnerships.length > 0) {
            parameter.pops = selectedPartnerships;
          }
          delete parameter.populations;
          delete parameter.parameterObj;
          delete parameter.selectAll;
        });

        console.log('$scope.state.program', $scope.state.program);

        $modalInstance.close($scope.state.program);
      }
    };

    initialize();

  });

});
