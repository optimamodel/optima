/**
* This directive triggers 'onAfterRender' once it's redered.
* Also can evaluate arbitrary code for people that know what they are doing
* Do not abuse the expression evaluator by making the view do things the controller should do!
*/

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