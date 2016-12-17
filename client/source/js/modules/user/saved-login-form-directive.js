define(['./module'], function (module) {
  'use strict';

  /**
   * Directive-based hack for automatically filled forms of sign in
   */
  module.directive('savedLoginForm', function ($timeout) {
    return {
      require: 'ngModel',
      link: function (scope, elem, attr, ngModel) {
        var origVal = elem.val();
        $timeout(function () {
          var newVal = elem.val();
          if (ngModel.$pristine && origVal !== newVal) {
            ngModel.$setViewValue(newVal);
          }
        }, 500);
      }
    };
  });
});
