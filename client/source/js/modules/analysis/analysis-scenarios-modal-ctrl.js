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

    $scope.addParameter = function() {
      var entry = {'keys':['condom','reg'], 'pop':0, 'startyear':2010,'endyear':2015,'startval':-1,'endval':1};
      scenario.pars.push(entry);
    };

  });

});
