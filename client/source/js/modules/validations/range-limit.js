define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.range-limit', [])
    .directive('rangeLimit', [function () {
      return {
        require: 'ngModel',
        scope: {
          rangeLimit: '='
        },
        link: function (scope, element, attrs, ctrl) {

          var updateValidity = function (value, lowerLimit, upperLimit) {

            value = parseFloat(value)
            lowerLimit = parseFloat(lowerLimit)
            upperLimit = parseFloat(upperLimit)

            var smaller = (!isNaN(lowerLimit) ? value >= lowerLimit : true);
            var bigger = (!isNaN(upperLimit) ? value <= upperLimit : true);
            var equal = !isNaN(upperLimit) && !isNaN(lowerLimit) && upperLimit === lowerLimit;
            var isValid = !isNaN(value) && smaller && bigger && !equal;

            ctrl.$setValidity('rangeLimit', isValid);
          };

          var validator = function (value) {
            if (scope.rangeLimit !== undefined) {
              updateValidity(value, scope.rangeLimit[0], scope.rangeLimit[1]);
            }
            return value;
          };

          // updated validity as soon as the input value changes
          ctrl.$parsers.unshift(validator);
          ctrl.$formatters.unshift(validator);

          // updated validity also when the value to compare changes
          scope.$watch('rangeLimit', function (rangeLimit) {
            updateValidity(ctrl.$modelValue, rangeLimit[0], rangeLimit[1]);
          });

        }
      };
    }]);
});
