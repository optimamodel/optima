define(['angular'], function (angular) {

  'use strict';

  var module = angular.module('app.population-modal', []);


  module.controller('ProjectCreatePopulationModalController', function (
      $scope, $modalInstance, population, populations, modalService) {

    function initialize() {
      $scope.isNew = !population.name;
      $scope.population = angular.copy(population);
      $scope.population.active = true;
      $scope.otherPopulations = _.filter(populations, function(p) {
        return p.short !== $scope.population.short;
      });
    }

    $scope.doesPopulationAttrClash = function(key) {
      return _.find($scope.otherPopulations, function(otherPopulation) {
        return $scope.population[key] === otherPopulation[key];
      });
    };

    $scope.isFormValid = function() {
      return (!$scope.doesPopulationAttrClash('name')
          && !$scope.doesPopulationAttrClash('short')
          && !$scope.PopulationForm.$invalid);
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        modalService.inform(undefined, undefined, 'Please fill in the form correctly');
      } else {
        console.log('submit', $scope.population);
        $modalInstance.close($scope.population);
      }
    };

    initialize();

  });

});
