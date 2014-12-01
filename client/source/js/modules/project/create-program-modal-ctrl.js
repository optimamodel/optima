define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreateProgramModalController', function ($scope,
    $modalInstance, program, availableParameters, populations) {

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !program.name;

      // make sure the names are exactly the objects as in the list for the
      // select to show the initial entries (angular compares with ===)
      _(program.parameters).each(function(entry) {
        entry.value.signature = findParameters(availableParameters, entry.value.signature).keys;

        var foundPopulation = findPopulation(populations, entry.value.pops);
        if (foundPopulation) {
          entry.value.pops = foundPopulation.internal_name;
        }
      });

      $scope.program = program;
      $scope.program.active = true;

      $scope.availableParameters = availableParameters;
      $scope.populations = populations;
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
    * Finds a population entry based on the internal_name
    */
    var findPopulation = function(populations, internalName) {
      return _(populations).find(function(population) {
        return areEqualArrays([population.internal_name], internalName);
      });
    };

    $scope.addParameter = function() {
      var entry = {value: {signature: [], pops: []}};
      $scope.program.parameters = $scope.program.parameters || [];
      $scope.program.parameters.push(entry);
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.program);
      }
    };

    initialize();

  });

});
