define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.error-custom-messages', []).directive('errorCustomMessages', function () {
    return {
      restrict: 'EA',
      replace: false,
      transclude: false,
      scope: {
        for: '@',
        rules: "="
      },
      require: '^form',
      template: '<div ng-if="errorMessages().length>0" class="error-hint"><div ng-repeat="message in errorMessages()">{{message}}</div></div>',
      link: function ($scope, $elem, $attrs, form) {
        /**
         * Returns the error messages in invalid state or an empty array if none is found.
         */
        $scope.errorMessages = function () {
          if (form && form[$scope.for].$dirty) {
            return _($scope.rules).select(function (eachRule, key) {
              // Has the rule and the rule is denoucing invalid state?
              return _(form[$scope.for].$error).has(key) && form[$scope.for].$error[key];
            });
          }
        };
      }
    };
  });
});
