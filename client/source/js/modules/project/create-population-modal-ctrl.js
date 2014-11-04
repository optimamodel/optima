define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreatePopulationModalController', function ($scope, $modalInstance, population) {

    $scope.isNew = !population.name;

    $scope.population = population;

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Please fill in the form correctly');
      }

      $modalInstance.close($scope.population);
    };

  });

});
