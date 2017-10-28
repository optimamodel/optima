define(['angular', 'underscore'], function (angular, _) {

  'use strict';

  var module = angular.module('app.program-modal', []);

  module.controller('ProgramModalController', function (
    $scope, $modalInstance, program, populations, programList, modalService,
    parameters, categories, openProject) {

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    function deepCopy(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
    }

    function isNonemptyList(l) {
      return (!_.isUndefined(l) && !_.isUndefined(l.length) && l.length > 0);
    }

    function initialize() {

      $scope.state = {
        selectAll: false,
        isNew: !program.name,
        populations: deepCopy(populations), // all possible populations in the program
        parameters: parameters, // all possible parameters
        categories: categories,
        program: program,
        openProject: openProject,
        showAddData: false,
        newAddData: {},
        progPopReadOnly: false
      };

      /**
       All populations for the project will be listed for
       the program for user to select from.

       Logic below will:

       1. If there is some parameter in the program which
          have 'tot' population then all populations should
          be selected for the program.
       2. set the populations which have already been selected
          for the program as active.
       3. if all the populations have been selected for the
          program selectAll will be set to true.
       */

      var isAnyTargetparForTotal = _.some(
        $scope.state.program.targetpars,
        function(par) { return par.pops.indexOf('tot') >= 0; }
      );

      console.log('ProgramModalController.init costcov', $scope.state.program.costcov);
      $scope.years = _.range(openProject.startYear, openProject.endYear+1);

      if (isAnyTargetparForTotal) {
        $scope.state.progPopReadOnly = true;
        $scope.state.selectAll = true;
        $scope.clickAllTargetPopulations();
      } else {
        console.log('ProgramModalController.init program', $scope.state.program);
        if (isNonemptyList($scope.state.program.populations)) {
          _.forEach($scope.state.populations, function(population) {
            population.active = (
              $scope.state.program.populations.length === 0)
               || ($scope.state.program.populations.indexOf(population.short) > -1);
          });
          $scope.state.selectAll = !_.find($scope.state.populations, function(population) {
            return !population.active;
          })
        } else {
          $scope.state.program.populations = [];
        }
      }

      _.forEach($scope.state.program.targetpars, setAttrOfPar);
      console.log('ProgramModalController.init targetpars', $scope.state.program.targetpars);

      // Set the program as active
      $scope.state.program.active = true;

      // Add new programs to Other category
      if ($scope.state.isNew) {
        $scope.state.program.category = 'Other';
      }

      // Initialize eligibility criteria
      if(!$scope.state.program.criteria) {
        $scope.state.program.criteria = {
          hivstatus: 'allstates', // can also be list of strings
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
    }

    /**
     * Section below will initialize parameters for program, it will:
     * 1. add temporary attr to each parameter, it will have parameter details from api /parameters
     * 2. if attr has partnerships, set them as added if they are already added to program
     * 3. if attr has no partnerships initialize parameter will populations from project populations,
     *    set the populations which have already been added to the program->parameters as added.
     * 4. set selectAll if all the partnerships / populations have already been added for the parameter.

      state.program
        acitve:
        name:
        short:
        category:
        criteria
        optmizable:
        targetpars:
          - param: string
            pops: string -or- pop: string or 2-tuple(string)
            attr:
              pships: list of pop
              name:
              param:
              by:
        costcov:
        ccopars:

     */
    function setAttrOfPar(targetpar) {

      var attr = _.find(parameters, function(parameter) {
        return targetpar.param === parameter.param;
      });
      if (_.isUndefined(attr)) {
        return;
      }
      targetpar.attr = deepCopy(attr);

      if (attr.by == "pship") {

        targetpar.attr.pships = deepCopy(targetpar.attr.pships);

        _.forEach(targetpar.attr.pships, function(pship) {
          _.forEach(targetpar.pops, function(pop) {
            if(angular.equals(pship, pop)) {
              pship.added = true;
            }
          });
        });

        targetpar.selectAll =
          targetpar.attr.pships
            && targetpar.pops
            && (targetpar.attr.pships.length === targetpar.pops.length);

      } if (targetpar.attr.by === 'tot') {

        targetpar.pops = ['tot'];
        targetpar.attr.populations = [];

      } else if (attr.by == "pop") {

        targetpar.attr.selectAll =
          targetpar.attr.populations
          && $scope.state.populations
          && (targetpar.attr.populations.length === targetpar.pops.length);

        targetpar.attr.populations = [];

        _.forEach($scope.state.populations, function(population) {
          var isInTargetpar =_.find(
            targetpar.pops,
            function(pop) { return pop === population.short });
          var newPopulation = angular.copy(population);
          if (isInTargetpar) {
            newPopulation.added = true;
          } else {
            newPopulation.added = false;
          }
          targetpar.attr.populations.push(newPopulation);
        });

      } else {
        console.log('setAttrOfPar error in setting targetpar');
      }

      console.log('setAttrOfPar targetpar', targetpar);

    }

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
      var newTargetPar = {active: true};
      setAttrOfPar(newTargetPar);
      $scope.state.program.targetpars.push(newTargetPar);
    };

    /**
     * Ensures populations ard partnerships are added to attr. Assumes that
     * target.param has just been set by a selector. So will need to
     * clear targetpar.pops and reset the attr for checkboxes     *
     */
    $scope.changeParameter = function(targetpar) {
      targetpar.pops = [];
      targetpar.attr = {};
      setAttrOfPar(targetpar);
    };

    $scope.clickAllPopulationsOfParameter = function(parameter) {
      _.forEach(parameter.attr.populations, function(population) {
        population.added = parameter.attr.selectAll;
      });
    };

    $scope.clickAnyPopulationOfParameter = function(parameter, populations) {
      parameter.attr.selectAll = !_.some(populations, function(population) {
        return !population.added;
      });
    };

    $scope.clickAllPartnershipsOfParameter = function(parameter) {
      _.forEach(parameter.attr.pships, function(pship) {
        pship.added = parameter.attr.selectAll;
      });
    };

    $scope.clickAnyPartnershipOfParameter = function(parameter, pships) {
      parameter.attr.selectAll = !_.some(pships, function(pship) {
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
    $scope.addHistoricalYearCostcovData = function () {
      console.log('addHistoricalYearCostcovData');
      if(!$scope.state.program.costcov) {
        $scope.state.program.costcov = [];
      }
      $scope.state.program.costcov.push({
        year: new Date().getFullYear(),
        cost: null,
        coverage: null,
      });
    };

    $scope.submit = function(form) {
      if (form.$invalid) {
        modalService.inform(undefined, undefined, 'Please fill in the form correctly');
      } else {

        $scope.state.showAddData = false;

        $scope.state.program.populations =
          _.filter(
            $scope.state.populations,
            function(population) {
              return population.active;
            })
          .map(function(population) {
              return population.short;
            });

        $scope.state.program.criteria.hivstatus = '';
        if ($scope.state.allHivStates) {
          $scope.state.program.criteria.hivstatus = 'allstates';
        } else {
          var stateShorts = [];
          _.each($scope.state.hivState, function(state, hivStateShort) {
            if (state) {
              stateShorts.push(hivStateShort);
            }
          });
          if (stateShorts.length > 2) {
            $scope.state.program.criteria.hivstatus = stateShorts;
          } else if (stateShorts.length == 1) {
            $scope.state.program.criteria.hivstatus = stateShorts[0];
          }
        }

        if ($scope.state.program.targetpars)

          /**
           * The code below will extract the population / parameter arrays to be
           * saved and will delete any unwanted data from it.
           */
          _.forEach($scope.state.program.targetpars, function(targetpar) {

            targetpar.param = targetpar.attr.param;
            var addedPopulations = _.filter(targetpar.attr.populations, function(population) {
              return population.added;
            });

            if (targetpar.attr.by !== 'tot' && addedPopulations && addedPopulations.length > 0) {
              targetpar.pops = addedPopulations.map(function(p) { return p.short; });
            } else {
              targetpar.pops = ['tot'];
            }

            var pships = _.filter(targetpar.attr.pships, function(p) { return p.added; });
            if (pships && pships.length > 0) {
              targetpar.pops = pships;
            }

            delete targetpar.attr;

          });

        $modalInstance.close($scope.state.program);
      }
    };

    initialize();

  });

});
