define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.common.after-render', [])
    .directive('afterRender', function($timeout) {
      var def = {
        restrict : 'A', 
        terminal : true,
        transclude : false,
        link : function(scope, element, attrs) {
          if (attrs) { scope.$eval(attrs.afterRender) }
            scope.$emit('onAfterRender')
        }
    };
    return def;
  });
});