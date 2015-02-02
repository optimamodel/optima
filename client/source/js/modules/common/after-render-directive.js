define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.common.after-render', [])
	.directive('afterRender', [ '$timeout', function($timeout) {
	var def = {
	    restrict : 'A', 
	    terminal : true,
	    transclude : true,
	    link : function(scope, element, attrs) {
	        $timeout(scope.$emit('rendered'), 0);
	    }
	};
	return def;
	}]);
});