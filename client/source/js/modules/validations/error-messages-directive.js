define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  return angular.module('app.validations.error-messages', []).directive('errorMessages', function () {
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
        var errorMessages = {
          'min': 'The minimum value must be <%= min %>.',
          'max': 'The maximum value can be <%= max %>.',
          'number': 'The field must be a number.',
          'required': 'The field <%= name %> is required.',
          'moreThan': 'The value must be greater than <%= moreThan %>.',
          'lessThan': 'The value must be less than <%= lessThan %>.'
        };

        /**
         * Returns the rendered error messages in invalid state or an empty array if none is found.
         */        
        $scope.errorMessages = function () {
          if (form && form[$scope.for].$dirty) {
            // Collects the templates with the error messages that are actually found as invalid and
            // rejects (using _.compact) anything that might not be found there.
            return _.compact(_(form[$scope.for].$error).map(function (isInvalid, errorKey) {
              if (isInvalid) {
                if ( _($scope.rules).has(errorKey) && _(errorMessages).has(errorKey)) {
                  var templateScope = {};
                  templateScope[errorKey] = $scope.rules[errorKey];
                  return _.template(
                            errorMessages[errorKey], 
                            templateScope);
                }
              }
            }));
          }
        };
      }
    }
  });
});
