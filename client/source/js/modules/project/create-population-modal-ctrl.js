define(['./module', 'angular'], function (module, angular) {
  'use strict';

  module.controller('ProjectCreatePopulationModalController', function ($scope, $modalInstance, population, populations, modalService) {

    // Initializes relevant attributes
    $scope.isNew = !population.name;
    // in order to not perform changes directly on the final value here is created a copy
    $scope.population = angular.copy(population);
    $scope.population.active = true;

    populations = _.filter(populations, function(p) { return p.short_name !== $scope.population.short_name; });

    $scope.populationExists = function(key){
      return _.find(populations, function (population) {
        return $scope.population[key] === population[key];
      });
    };

    $scope.isFormValid = function(){
      if(!$scope.populationExists('name') && !$scope.populationExists('short_name') && !$scope.PopulationForm.$invalid){
        return true;  
      }else{
        return false;
      }
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined,undefined, 'Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.population);
      }
    };

  });

});
