define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.common.after-render', [])
	.directive('afterRender', [ '$timeout', function($timeout) {
	var def = {
	    restrict : 'A', 
	    terminal : true,
	    transclude : false,
	    link : function(scope, element, attrs) {
	    	// triggers the rendered event 
	        scope.$emit('rendered');

	        if (attrs) { console.warn(scope.$eval(attrs.afterRender)) }
	    }
	};
	return def;
	}]);
});