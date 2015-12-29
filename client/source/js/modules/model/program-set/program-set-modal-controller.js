define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetModalController', function ($scope, $modalInstance, program, availableParameters, populations, modalService) {

    // in order to not perform changes directly on the final value here is created a copy
    var programCopy = angular.copy(program);

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !programCopy.name;
      $scope.selectAll = false;
      $scope.availableParameters = angular.copy(availableParameters);
      $scope.populations = angular.copy(populations);

      $scope.initializeAllCategories();

      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(programCopy.parameters).each(function(entry) {
        entry.value.signature = findParameters($scope.availableParameters, entry.value.signature).keys;

        var foundPopulation = findPopulation($scope.populations, entry.value.pops);
        if (foundPopulation) {
          entry.value.pops = foundPopulation.value;
        }
      });

      $scope.program = programCopy;
      $scope.program.active = true;
      if (!$scope.program.populations) {
        $scope.program.populations = populations;
      }
      if ($scope.isNew) { $scope.program.category = 'Other'; }
    };

    $scope.selectAllPopulations = function() {
      _.forEach($scope.program.populations, function(population) {
        population.active = $scope.selectAll;
      });
    };

    $scope.selectAllEntryPopulations = function(entry, selectAll) {
      _.forEach(entry.value.pops, function(population) {
        population.active = selectAll;
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

    /*
    * Finds a population entry based on the value
    */
    var findPopulation = function(populations, value) {
      return _(populations).find(function(population) {
        return areEqualArrays(population.value, value);
      });
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
        });
        _.forEach(selected_populations, function(population) {
          delete population.active;
        });

        $scope.program.populations = selected_populations;
        $scope.program.parameters = _($scope.program.parameters).filter(function (item) {
          delete item.selectAll;
          item.value.pops = _.filter(item.value.pops, function(population) {
            return population.active;
          });
          _.forEach(item.value.pops, function(population) {
            delete population.active;
          });
          return item.value.signature.length && item.value.pops.length;
        });

        $modalInstance.close($scope.program);
      }
    };

    initialize();

  });

});
