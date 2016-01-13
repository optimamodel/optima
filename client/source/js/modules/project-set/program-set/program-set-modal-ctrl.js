define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetModalController', function ($scope, $modalInstance, program, availableParameters, populations, programList, modalService) {

    var hivstatus = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids', 'allstates'];

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !program.name;
      $scope.availableParameters = angular.copy(availableParameters);
      $scope.populations = angular.copy(populations);
      $scope.selectAll = true;
      _.forEach($scope.populations, function(population) {
        // if populations are empty, that means all populations by default are enabled for that program (by convention)
        // if no populations are enabled for the program, then it cannot be active (because it's not used :) )
        if(program.populations) {
          population.active = (program.populations.length==0) || (program.populations.indexOf(population.short_name) > -1);
          if (!population.active) $scope.selectAll = false;
        }
      });

      $scope.initializeAllCategories();

      var oldPops;
      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(program.parameters).each(function(entry) {
        /* entry.value.signature = findParameters($scope.availableParameters, entry.value.signature).keys;

        oldPops = entry.value.pops;
        if (oldPops.length==1 && oldPops[0] == "") oldPops = [];
        entry.selectAll = true;
        entry.value.pops = angular.copy(populations);
        _.each(entry.value.pops, function(pop) {
          // same here: if pops is empty => all populations are enabled (by convention)
          // and if parameter is active, either one or all populations should be enabled
          // (unless its target populations aren't included in the project populations :) )
          pop.active = (oldPops.length==0) || (oldPops.indexOf(pop.short_name) > -1);
          if (!pop.active) entry.selectAll = false;
        });*/
      });

      $scope.program = program;
      $scope.program.active = true;
      if ($scope.isNew) { $scope.program.category = 'Other'; }


      $scope.eligibility = {
        pregnantFalse: !$scope.program.criteria.pregnant
      };

      if($scope.program.criteria.hivstatus && $scope.program.criteria.hivstatus === 'allstates') {
        $scope.eligibility.allstates = true;
      } else if($scope.program.criteria.hivstatus.length > 0) {
        _.each($scope.program.criteria.hivstatus, function(state) {
          $scope.eligibility[state] = true;
        });
      }
    };

    $scope.setEligibility = function(selectedEligibility) {
      if(selectedEligibility === 'allstates') {
        $scope.eligibility.acute = false;
        $scope.eligibility.gt500 = false;
        $scope.eligibility.gt350 = false;
        $scope.eligibility.gt200 = false;
        $scope.eligibility.gt50 = false;
        $scope.eligibility.aids = false;
      } else {
        $scope.eligibility.allstates = false;
      }
    };

    $scope.selectAllPopulations = function() {
      _.forEach($scope.populations, function(population) {
        population.active = $scope.selectAll;
      });
    };

    $scope.selectAllEntryPopulations = function(entry) {
      _.forEach(entry.value.pops, function(population) {
        population.active = entry.selectAll;
      });
    };

    /*
    * Returns true of the two provided arrays are identic
    */
    var areEqualArrays = function(arrayOne, arrayTwo) {
      return _(arrayOne).every(function(element, index) {
        return element === arrayTwo[index];
      });
    };

    /*
    * Finds a paramter entry based on the keys
    */
    var findParameters = function(parameters, keys) {
      return _(parameters).find(function(parameterEntry) {
        return areEqualArrays(parameterEntry.keys, keys);
      });
    };

    $scope.isUniqueName = function (name, programForm) {
      var exists = _(programList).some(function(program) {
        return program.name == name && program.id !== $scope.program.id;
      });
      programForm.programName.$setValidity("programExists", !exists);
      return exists;
    };

    $scope.initializeAllCategories = function () {
      $scope.allCategories = [
        'Prevention',
        'Care and treatment',
        'Management and administration',
        'Other'
      ];
    };

    $scope.addParameter = function () {
      var entry = {value: {signature: [], pops: angular.copy(populations)}, active: true};
      entry.selectAll = true;
      _.each(entry.value.pops, function(pop) {
          // enable every population by default, there is no additional info in the parameter anyway
          pop.active = true;
        });
      $scope.program.parameters = $scope.program.parameters || [];
      $scope.program.parameters.push(entry);
    };

    /**
     * Removes the parameter at the given index (without asking for confirmation).
     */
    $scope.removeParameter = function ($index) {
      program.parameters.splice($index,1);
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined,'Please fill in the form correctly');
      } else {
        // filter out empty parameters
        var selected_populations = _.filter($scope.populations, function(population) {
          return population.active;
        }).map(function(population) {
          return population.short_name;
        });

        $scope.program.criteria.hivstatus = _.filter(hivstatus, function(state) {
          return $scope.eligibility[state];
        }).map(function(state) {
          return state;
        });

        $scope.program.populations = selected_populations;
        /*$scope.program.parameters = _($scope.program.parameters).filter(function (item) {
          delete item.selectAll;
          item.value.pops = _.filter(item.value.pops, function(population) {
            return population.active;
          }).map(function(population) {
            return population.short_name;
          });
          return item.value.signature.length && item.value.pops.length;
        });*/

        console.log('$scope.program', $scope.program);

        $modalInstance.close($scope.program);
      }
    };

    initialize();

  });

});
