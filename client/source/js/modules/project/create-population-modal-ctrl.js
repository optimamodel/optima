define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ProjectCreatePopulationModalController', function ($scope, $modalInstance, population) {

    // Initializes relevant attributes
    $scope.isNew = !population.name;
    // in order to not perform changes directly on the final value here is created a copy
    $scope.population = angular.copy(population);
    $scope.population.active = true;

    $scope.submit = function (form) {
      if ($scope.population.male && $scope.population.female) {
        alert('Please select either male, female or none of them.');
      } else if (form.$invalid) {
        alert('Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.population);
      }
    };

  });

});
