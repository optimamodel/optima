define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.limit', [])
    .directive('limitValidator', [function () {
      return {
        require: 'ngModel',
        scope: {
          lower: '=',
          upper: '='
        },
        link: function (scope, element, attrs, ctrl) {

          var updateValidity = function (value, lower, upper) {
            var currentValue = parseInt(value);
            var isValid = value !== undefined && value.toString().length === 4 && (lower && currentValue >= lower) && (upper && currentValue <= upper);
            ctrl.$setValidity('limitValidator', isValid);
          };

          var validator = function (value) {
            updateValidity(value, scope.lower, scope.upper);
            return value;
          };

          // updated validity as soon as the input value changes
          ctrl.$parsers.unshift(validator);
          ctrl.$formatters.unshift(validator);

          // updated validity also when the value to compare changes
          scope.$watch('[lower, upper]', function (limits) {
            updateValidity(ctrl.$modelValue, limits[0], limits[1]);
          });

        }
      };
    }]);
});
