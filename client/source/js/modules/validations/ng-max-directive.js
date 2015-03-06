define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.ng-max', []).directive('ngMax', function () {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function (scope, element, attr, ctrl) {

        scope.initialize = function () {
          scope.$watch(attr.ngMax, function () {
            ctrl.$setViewValue(ctrl.$viewValue);
          });

          ctrl.$parsers.push( scope.maxValidator );
          ctrl.$formatters.push( scope.maxValidator );
        };

        /**
         * Returns the value and sets validity in true if value didn't surpass the upper limit.
         * Otherwise sets validity in false and returns undefined.
         */
        scope.maxValidator = function (value) {
          var max = scope.$eval(attr.ngMax) || Infinity;
          if (!scope.isValidable(value) && value > max) {
              ctrl.$setValidity('ngMax', false);
              return undefined;
          } else {
              ctrl.$setValidity('ngMax', true);
              return value;
          }
        };

        /**
         * Returns true if value is not something we can validate against max.
         */
        scope.isValidable = function (value) {
            return angular.isUndefined(value) || value === '' || value === null || value !== value;
        };

        scope.initialize();
      }
    };
  });
});
