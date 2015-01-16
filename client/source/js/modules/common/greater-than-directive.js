define(['angular'], function (angular) {
  'use strict';
  return angular.module('app.common.greater-than', []).directive('greaterThan', function ($parse) {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function ($scope, $elem, $attrs, $ctrl) {
        $ctrl.$parsers.unshift(function (value) {
          var valid = true;
          if (value) {
            valid = parseInt(value) > parseInt($parse($attrs.greaterThan)($scope));
            $ctrl.$setValidity('greaterThan', valid);
          }
          return valid ? value : undefined;
        });
      }
    }
  });
});