define(['./module'], function (module) {
  'use strict';

  module.controller('AnalysisScenariosModalController', function ($scope, $modalInstance, scenario) {

    $scope.isNew = !scenario.name;

    $scope.scenario = scenario;

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Your valiant attempts to fill in the form correctly have failed. Please try again');
      }

      $modalInstance.close($scope.scenario);
    };

  });

});
