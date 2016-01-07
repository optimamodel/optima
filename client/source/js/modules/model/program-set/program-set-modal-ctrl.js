define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetModalController', function ($scope, $modalInstance, program, availableParameters, populations, programList, modalService) {

    // in order to not perform changes directly on the final value here is created a copy
    var programCopy = angular.copy(program);
    if(programCopy.name && !programCopy.id) {
      programCopy.name = programCopy.name + ' - Copy'
    }

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !programCopy.name;
      $scope.availableParameters = angular.copy(availableParameters);
      $scope.populations = angular.copy(populations);
      $scope.selectAll = true;
      _.forEach($scope.populations, function(population) {
        if(programCopy.populations) {
          population.active = (programCopy.populations.length==0) || (programCopy.populations.indexOf(population.short_name) > -1);
          if (!population.active) $scope.selectAll = false;
        } else {
          $scope.selectAll = false;
        }
      });

      $scope.initializeAllCategories();

      var oldPops;
      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(programCopy.parameters).each(function(entry) {
        entry.value.signature = findParameters($scope.availableParameters, entry.value.signature).keys;

        oldPops = entry.value.pops;
        if (oldPops.length==1 && oldPops[0] == "") oldPops = [];
        entry.selectAll = true;
        entry.value.pops = angular.copy(populations);
        _.each(entry.value.pops, function(pop) {
          pop.active = (oldPops.length==0) || (oldPops.indexOf(pop.short_name) > -1);
          if (!pop.active) entry.selectAll = false;
        });
      });

      $scope.program = programCopy;
      $scope.program.active = true;
      if ($scope.isNew) { $scope.program.category = 'Other'; }
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
      $scope.program.parameters = $scope.program.parameters || [];
      $scope.program.parameters.push(entry);
    };

    /**
     * Removes the parameter at the given index (without asking for confirmation).
     */
    $scope.removeParameter = function ($index) {
      programCopy.parameters.splice($index,1);
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

        $scope.program.populations = selected_populations;
        $scope.program.parameters = _($scope.program.parameters).filter(function (item) {
          delete item.selectAll;
          item.value.pops = _.filter(item.value.pops, function(population) {
            return population.active;
          }).map(function(population) {
            return population.short_name;
          });
          return item.value.signature.length && item.value.pops.length;
        });

        $modalInstance.close($scope.program);
      }
    };

    initialize();

  });

});
