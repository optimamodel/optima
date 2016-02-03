define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.year', [])
    .directive('yearValidator', [function () {
      return {
        require: 'ngModel',
        scope: {
          fromYear: '=',
          toYear: '='
        },
        link: function (scope, element, attrs, ctrl) {

          var updateValidity = function (value, fromYear, toYear) {
            if (toYear === undefined) {
              toYear = 2050
            }
            var currentValue = parseInt(value);
            var isValid = value !== undefined && value.toString().length === 4 && (fromYear && currentValue >= fromYear) && (toYear && value <= toYear);
            ctrl.$setValidity('yearValidator', isValid);
          };

          var validator = function (value) {
            updateValidity(value, scope.fromYear, scope.toYear);
            return value;
          };

          // updated validity as soon as the input value changes
          ctrl.$parsers.unshift(validator);
          ctrl.$formatters.unshift(validator);

          // updated validity also when the value to compare changes
          scope.$watch('[fromYear, toYear]', function (years) {
            updateValidity(ctrl.$modelValue, years[0], years[1]);
          });

        }
      };
    }]);
});
