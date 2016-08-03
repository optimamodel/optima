 define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramModalController', function ($scope, $modalInstance, program, populations, programList, modalService, parameters, categories, openProject) {
    // Default list of criteria
    var hivstatus = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids', 'allstates'];

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    // Initializes controller state and sets some default values in the program
    var initialize = function () {

      $scope.state = {
        selectAll: false,
        isNew: !program.name,
        populations: angular.copy(populations),
        parameters: parameters,
        categories: categories,
        program: program,
        openProject: openProject,
        eligibility: {
          pregnantFalse: true,
          allstates: true
        },
        showAddData: false,
        newAddData: {},
        progPopReadOnly: false
      };

      /**
       * All populations for the project will be listed for the program for user to select from.
       * Logic below will:
       * 1. If there is some parameter in the program which hae 'tot' population then all populations should be selected for the program.
       * 2. set the populations which have already been selected for the program as active.
       * 3. if all the populations have been selected for the program selectAll will be set to true.
       */
      var isTot = _.some($scope.state.program.targetpars, function(parameter) {
        return parameter.pops.indexOf('tot') >= 0;
      });
      if(isTot) {
        $scope.state.progPopReadOnly = true;
        $scope.state.selectAll = true;
        $scope.clickAllTargetPopulations();
      } else {
        if(program.populations && program.populations.length > 0) {
          _.forEach($scope.state.populations, function(population) {
            population.active = (program.populations.length === 0) || (program.populations.indexOf(population.short) > -1);
          });
          $scope.state.selectAll = !_.find($scope.state.populations, function(population) {
            return !population.active;
          })
        }
      }

      /**
       * Section below will initialize parameters for program, it will:
       * 1. add temporary parameterObj to each parameter, it will have parameter details from api /parameters
       * 2. if parameterObj has partnerships, set them as added if they are already added to program
       * 3. if parameterObj has no partnerships initialize parameter will populations from project populations,
       *    set the populations which have already been added to the program->parameters as added.
       * 4. set selectAll if all the partnerships / populations have already been added for the parameter.
       */
      _.forEach($scope.state.program.targetpars, function(parameter) {
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
	      } else if(parameter.pops && parameter.pops.length > 0 && parameter.pops[0]!="tot") {
          parameter.populations = angular.copy($scope.state.populations);
          _.forEach(parameter.populations, function(population) {
            if (_.find(parameter.pops, 
                       function(pop) { return pop === population.short })) {
              population.added = true;
            } else {
              population.added = false;
            }
          })
          parameter.selectAll = parameter.populations && $scope.state.populations && parameter.populations.length === parameter.pops.length;
        }
      });

      // Set the program as active
      $scope.state.program.active = true;

      // Add new programs to Other category
      if ($scope.state.isNew) {
        $scope.state.program.category = 'Other';
      }

      // Initialize eligibility criteria
      if(!$scope.state.program.criteria) {
        $scope.state.program.criteria = {
          hivstatus: 'allstates',
          pregnant: false
        }
      }

      $scope.state.allHivStates = $scope.state.program.criteria.hivstatus == 'allstates';
      $scope.hivStates = [
        {short: 'acute', name: 'Acute infections'},
        {short: 'gt500', name: 'CD4 > 500'},
        {short: 'gt350', name: 'CD4 350-500'},
        {short: 'gt200', name: 'CD4 200-350'},
        {short: 'gt50', name: 'CD4 50-200'},
        {short: 'aids', name: 'CD4 <50'},
      ];
      $scope.state.hivState = {};
      _.each($scope.hivStates, function(state) {
        $scope.state.hivState[state.short] = $scope.state.allHivStates;
      });
    };

    $scope.clickAllHivStates = function() {
      _.forEach($scope.state.hivState, function(state, key) {
        $scope.state.hivState[key] = $scope.state.allHivStates;
      });
    };

    // Ensures state.selectAll responds to clicking any other population
    $scope.clickAnyHivState = function() {
      $scope.state.allHivStates = !_.some(
        $scope.state.hivState, function(state) { return !state; });
    };

    // Function to select / unselect all populations
    $scope.clickAllTargetPopulations = function() {
      _.forEach($scope.state.populations, function(population) {
        population.active = $scope.state.selectAll;
      });
    };

    // Ensures state.selectAll responds to clicking any other population
    $scope.clickAnyTargetPopulation = function() {
      $scope.state.selectAll = true;
      _.forEach($scope.state.populations, function(population) {
        if(!population.active) {
          $scope.state.selectAll = false;
        }
      });
    };

    $scope.checkClashingProgramName = function (name, programForm) {
      var exists = _(programList).some(function(program) {
        return program.name == name && program.id !== $scope.state.program.id;
      });
      programForm.programName.$setValidity("programExists", !exists);
      return exists;
    };

    // Add a new parameter
    $scope.addParameter = function() {
      if ($scope.state.program.targetpars == undefined) {
        $scope.state.program.targetpars = [];
      }

      $scope.state.program.targetpars.push({active: true});
    };

    // Ensures populations ard partnerships are added to parameterObj
    $scope.changeParameter = function(parameter) {
      if(parameter.parameterObj.by === 'tot'){
        parameter.populations = [];
      }else{
        if(!parameter.pships || parameter.pships.length === 0) {
          parameter.populations = $scope.state.populations;
        }
      }
    };

    $scope.clickAllPopulationsOfParameter = function(parameter) {
      _.forEach(parameter.populations, function(population) {
        population.added = parameter.selectAll;
      });
    };

    $scope.clickAnyPopulationOfParameter = function(parameter, populations) {
      parameter.selectAll = !_.some(populations, function(population) {
        return !population.added;
      });
    };

    $scope.clickAllPartnershipsOfParameter = function(parameter) {
      _.forEach(parameter.parameterObj.pships, function(pship) {
        pship.added = parameter.selectAll;
      });
    };

    $scope.clickAnyPartnershipOfParameter = function(parameter, pships) {
      parameter.selectAll = !_.some(pships, function(pship) {
        return !pship.added;
      });
    };

    // Function to remove a parameter
    $scope.removeParameter = function ($index) {
      program.targetpars.splice($index,1);
    };

    // Function to remove additional data
    $scope.deleteAddData = function (addData) {
      var indexOfData = $scope.state.program.costcov.indexOf(addData);
      $scope.state.program.costcov.splice(indexOfData,1);
    };

    // Function to add additional data
    $scope.addHistoricalData = function () {
      if($scope.state.newAddData.year && $scope.state.newAddData.cost >= 0 && $scope.state.newAddData.coverage >= 0) {
        if(!$scope.state.program.costcov) {
          $scope.state.program.costcov = [];
        }
        $scope.state.program.costcov.push($scope.state.newAddData);
        $scope.state.newAddData = {};
        $scope.state.showAddData = false;
      }
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined,'Please fill in the form correctly');
      } else {

        $scope.state.showAddData = false;

        $scope.state.program.populations = _.filter($scope.state.populations, function(population) {
          return population.active;
        }).map(function(population) {
          return population.short;
        });
        
        $scope.state.program.criteria.hivstatus = _.filter(hivstatus, function(state) {
          return $scope.state.eligibility[state];
        }).map(function(state) {
          return state;
        });
        // tot
        if($scope.state.program.targetpars)

        /**
         * The code below will extract the population / parameter arrays to be
         * saved and will delete any unwanted data from it.
         */
        _.forEach($scope.state.program.targetpars, function(parameter) {
          
          parameter.param = parameter.parameterObj.short;
          var addedPopulations = _.filter(parameter.populations, function(population){
            return population.added;
          });

          if(parameter.parameterObj.by !== 'tot' && addedPopulations && addedPopulations.length > 0) {
            parameter.pops = addedPopulations.map(function (population) {
              return population.short;
            });
          }else{
            parameter.pops = ['tot'];
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
        
        $modalInstance.close($scope.state.program);
      }
    };

    initialize();

  });

});
