define(['./module', 'angular'], function (module, angular) {

  'use strict';

  module.controller('ProjectCreatePopulationModalController', function (
      $scope, $modalInstance, population, populations, modalService) {

    function initialize() {
      $scope.isNew = !population.name;
      $scope.population = angular.copy(population);
      $scope.population.active = true;
      populations = _.filter(populations, function(p) {
        return p.short !== $scope.population.short;
      });
    }

    $scope.populationExists = function(key) {
      return _.find(populations, function(population) {
        return $scope.population[key] === population[key];
      });
    };

    $scope.isFormValid = function() {
      if (!$scope.populationExists('name')
          && !$scope.populationExists('short')
          && !$scope.PopulationForm.$invalid) {
        return true;
      } else {
        return false;
      }
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(
            undefined, undefined, 'Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.population);
      }
    };

    initialize();

  });

});
