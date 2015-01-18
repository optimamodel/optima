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

        // $scope.errorMessages = function () {
        //   if (form && form[$scope.for].$dirty) {
        //     // console.log(_.compact(_(form[$scope.for].$error)));
        //     console.log(form[$scope.for].$error);
        //     return _.compact(_(form[$scope.for].$error).map(function (e, key) {
        //       // debugger
        //       console.log(e,key);

        //       if (e) {
        //         var template = {};
        //         if ($scope.rules[key]!==undefined) {
        //           var ruleIsString = typeof $scope.rules[key] === 'string';
                  
        //             If the key is 'required', and the rules object contains 'name' property,
        //             show the field name in the error message
        //             otherwise just say that the field is required
                  
        //           if (key === 'required' && $scope.rules.name!==undefined) {
        //             template.name = $scope.rules.name;
        //           }
        //           else {
        //               debugger
        //               template[key] = ruleIsString ? $scope.rules[key] : $scope.rules[key].value;
        //           }
        //           if(errorMessages[key]!==undefined) {
        //               return _.template(ruleIsString ? errorMessages[key]:$scope.rules[key].message, template);
        //           }
        //         }
        //       }
        //     }));
        //   }
        // };

        /**
         * Returns the error messages in invalid state or an empty array if none is found.
         */        
        $scope.errorMessages = function () {
          if (form && form[$scope.for].$dirty) {
            return _($scope.rules).select(function (eachRule) { 
              // Has the rule and the rule is denoucing invalid state?
              return _(form[$scope.for].$error).has(eachRule) && form[$scope.for].$error[eachRule] 
              });
          }
        };
      }
    }
  });
});
