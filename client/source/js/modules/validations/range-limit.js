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

            value = parseInt(value)
            lowerLimit = parseInt(lowerLimit)
            upperLimit = parseInt(upperLimit)

            var smaller = (lowerLimit !== undefined ? value >= lowerLimit : true);
            var bigger = (upperLimit !== undefined ? value <= upperLimit : true);
            var equal = upperLimit !== undefined && lowerLimit !== undefined && upperLimit === lowerLimit;
            var isValid = value !== undefined && smaller && bigger && !equal;

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
