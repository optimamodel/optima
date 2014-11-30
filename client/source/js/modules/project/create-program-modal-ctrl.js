define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreateProgramModalController', function ($scope, $modalInstance, program) {

    // Initializes relevant attributes
    var initialize = function () {
      $scope.isNew = !program.name;
      $scope.program = program;
      $scope.program.active = true;
    };

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Please fill in the form correctly');
      } else {
        $modalInstance.close($scope.program);
      }
    };

    $scope.paramSpec = function (p) {
      var name = p.name;
      if (p.value.pops.length > 0) {
        name += ': ' + p.value.pops.join(' ');
      }
      return name;
    };

    initialize();

  });

});
