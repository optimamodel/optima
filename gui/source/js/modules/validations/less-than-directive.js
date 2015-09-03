define(['angular'], function (module) {
  'use strict';

  return angular.module('app.validations.less-than', [])
    /**
     * Adds a less than validator to an input element.
     *
     * The input element is only valid if the actual value is smaller
     * than the provided value through the directive.
     */
    .directive('lessThan', [function () {
      return {
        require: 'ngModel',
        scope: {
          lessThan: '='
        },
        link: function(scope, element, attrs, ctrl) {

          var updateValidity = function (lowValue, highValue) {
            var isValid = lowValue < highValue;
            var canBeEmpty = !element.required && (lowValue === undefined || highValue === undefined || lowValue == '' || lowValue == null);
            ctrl.$setValidity('lessThan', isValid || canBeEmpty);
          };

          var validator = function (value) {
            updateValidity(value, scope.lessThan);
            return value;
          };

          // updated validity as soon as the input value changes
          ctrl.$parsers.unshift(validator);
          ctrl.$formatters.unshift(validator);

          // updated validity also when the value to compare changes
          scope.$watch('lessThan', function(lessThanValue) {
            updateValidity(ctrl.$modelValue, lessThanValue);
          });
        }
      };
    }]);
});
