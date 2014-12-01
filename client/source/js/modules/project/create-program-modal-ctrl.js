define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreateProgramModalController', function ($scope,
    $modalInstance, program, availableParameters, populations) {

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !program.name;

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
    * Finds a scenario paramter based on the names
    */
    var findParameters = function(parameters, keys) {
      return _(parameters).find(function(parameterEntry) {
        return areEqualArrays(parameterEntry.keys, keys);
      });
    };

    $scope.addParameter = function() {
      var entry = {};
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
