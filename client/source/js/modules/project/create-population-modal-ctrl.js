define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreatePopulationModalController', function ($scope, $modalInstance, population) {

    // Initializes relevant attributes
    var initialize = function() {
      $scope.isNew = !population.name;
      $scope.population = population;
      $scope.population.active = true;
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.population);
      }
    };

    initialize();

  });

});
