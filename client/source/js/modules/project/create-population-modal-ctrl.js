define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreatePopulationModalController', function ($scope, $modalInstance, population) {

    $scope.isNew = !population.name;

    $scope.population = population;

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Your valiant attempts to fill in the form correctly have failed. Please try again');
      }

      $modalInstance.close($scope.population);
    };

  });

});
