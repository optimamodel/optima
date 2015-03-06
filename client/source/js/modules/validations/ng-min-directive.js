define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.ng-min', []).directive('ngMin', function () {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function (scope, element, attr, ctrl) {

        scope.initialize = function () {
          scope.$watch(attr.ngMin, function () {
            ctrl.$setViewValue(ctrl.$viewValue);
          });

          ctrl.$parsers.push( scope.minValidator );
          ctrl.$formatters.push( scope.minValidator );
        };

        /**
         * Returns the value and sets validity in true if value didn't surpass the upper limit.
         * Otherwise sets validity in false and returns undefined.
         */
        scope.minValidator = function (value) {
          var min = scope.$eval(attr.ngMin) || 0;
          if (!scope.isValidable(value) && value < min) {
              ctrl.$setValidity('ngMin', false);
              return undefined;
          } else {
              ctrl.$setValidity('ngMin', true);
              return value;
          }
        };

        /**
         * Returns true if value is not something we can validate against min.
         */
        scope.isValidable = function (value) {
            return angular.isUndefined(value) || value === '' || value === null || value !== value;
        };

        scope.initialize();
      }
    };
  });
});
