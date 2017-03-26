// Create a help popup
// Based on angularjs-slider
// Last modified: 2017-03-26 by cliffk

(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['angular'], factory);
  } else if (typeof module === 'object' && module.exports) {
    var angularObj = angular || require('angular');
    if ((!angularObj || !angularObj.module) && typeof angular != 'undefined') {
      angularObj = angular;
    }
    module.exports = factory(angularObj);
  } else {
    factory(root.angular); // Browser globals (root is window)
  }

}(this, function(angular) {
  var module = angular.module('helppopupModule', []) // Define module name

  .factory('RqSlieder', ['$timeout', '$document', '$window', '$compile', function($timeout, $document, $window, $compile) {
    var Slieder = function(scope, sliederElem) {
      this.scope = scope;
      this.lowValue = 0;
    };
    return Slieder;
  }])

  .directive('rqslieder', ['RqSlieder', function(RqSlieder) {
    'use strict';

    return {
      restrict: 'AE',
      replace: true,
      scope: {
        rqSliederModel: '=?',
      },
      templateUrl: 'js/modules/common/helppopup-template.html' ,

      link: function(scope, elem) {
        scope.slieder = new RqSlieder(scope, elem); //attach on scope so we can test it
      }
    };
  }]);

  return module.name
}));
