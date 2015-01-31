define(['angular', 'underscore'], function (angular, _) {
  'use strict';

  /* The 'show-always' attribute tells the directive if it should display the messages before the user started typing in the field */
  return angular.module('app.validations.error-messages', []).directive('errorMessages', function () {
    return {
      restrict: 'EA',
      replace: false,
      transclude: false,
      scope: {
        for: '@',
        showAlways:"=",
        rules: "="
      },
      require: '^form',
      template: '<div ng-if="errorMessages().length>0" class="error-hint"><div ng-repeat="message in errorMessages()">{{message}}</div></div>',
      link: function ($scope, $elem, $attrs, form) {
        var errorMessages = {
          'min': 'The minimum value is <%= min %>.',
          'max': 'The maximum value is <%= max %>.',
          'number': 'The field must be a number.',
          'required': 'The field <%= name %> is required.',
          'moreThan': 'The value must be greater than <%= moreThan %>.',
          'lessThan': 'The value must be less than <%= lessThan %>.'
        };

        /**
         * Returns the rendered error messages in invalid state or an empty array if none is found.
         */        
        $scope.errorMessages = function () {
          if (form && (form[$scope.for].$dirty || $scope.showAlways===true)) {
            return _.compact(_(form[$scope.for].$error).map(function (e, key) {
              if (e) {
                var template = {};
                if ($scope.rules[key]!==undefined) {
                  var ruleIsObject = typeof $scope.rules[key] === 'object';
                  /*
                    If the key is 'required', and the rules object contains 'name' property,
                    show the field name in the error message
                    otherwise just say that the field is required
                  */
                  if (key === 'required' && $scope.rules.name!==undefined) {
                    template.name = $scope.rules.name;
                  }
                  else {
                      template[key] = ruleIsObject ? $scope.rules[key].value : $scope.rules[key];
                  }
                  if(errorMessages[key]!==undefined) {
                      return _.template(ruleIsObject ? $scope.rules[key].message : errorMessages[key], template);
                  }
                }
              }
            }));
          }
        };
      }
    }
  });
});
