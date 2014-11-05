define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateProgramModalController', function ($scope, $modalInstance, PROGRAMS, program) {
    // Data

    $scope.newIndicator = {};

    $scope.summaryPrograms = angular.copy(PROGRAMS);

    // init

    // when editing program, it's needed to unwrap state from program
    if (program) {
      var activeSummaryProgram = _($scope.summaryPrograms).findWhere({ acronym: program.summary_program.acronym });

      $scope.program = {
        summary_program: activeSummaryProgram
      };

      $scope.program.program = _(activeSummaryProgram.programs).findWhere({ acronym: program.acronym });

      // overwrite default active property
      _($scope.program.program.indicators).each(function (item) {
        item.active = false;
      });

      // check items that were checked and add ones that were added manually
      _(program.indicators).each(function (presetIndicator) {
        var found = _($scope.program.program.indicators).find(function (defIndicator) {
          return defIndicator.name === presetIndicator.name;
        });

        if (found) {
          found.active = presetIndicator.active;
        } else {
          $scope.program.program.indicators.push(presetIndicator);
        }
      });
    } else {
      $scope.program = {};
    }

    // Methods

    $scope.submit = function (form) {
      if (form.$invalid) {
        alert('Please fill in the form correctly');
      }

      var program = _({}).extend(_($scope.program.program).omit('indicators'));
      program.summary_program = _($scope.program.summary_program).omit('programs');
      program.indicators = _($scope.program.program.indicators).where({ active: true });

      $modalInstance.close(program);
    };

    $scope.addIndicator = function ($event) {
      if ($event) {
        $event.preventDefault();
      }

      var indicator = {
        name: $scope.newIndicator.name,
        active: true
      };
      $scope.program.program.indicators.push(indicator);
      $scope.newIndicator.name = '';
    };

    // Watches

    $scope.$watch('program.program', function (value) {
      if (value && value.name) {
        angular.extend($scope.program, value);
      }
    });

  });

});
