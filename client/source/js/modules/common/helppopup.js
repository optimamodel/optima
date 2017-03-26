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

  .factory('RqSliederOptions', function() {
    var defaultOptions = {
      floor: 0,
      ceil: null, //defaults to rq-slieder-model
      step: 1,
      precision: 0,
      minRange: null,
      maxRange: null,
      pushRange: false,
      minLimit: null,
      maxLimit: null,
      id: null,
      translate: null,
      getLegend: null,
      stepsArray: null,
      bindIndexForStepsArray: false,
      draggableRange: false,
      draggableRangeOnly: false,
      showSelectionBar: false,
      showSelectionBarEnd: false,
      showSelectionBarFromValue: null,
      hidePointerLabels: false,
      hideLimitLabels: false,
      autoHideLimitLabels: true,
      readOnly: false,
      disabled: false,
      interval: 350,
      showTicks: false,
      showTicksValues: false,
      ticksArray: null,
      ticksTooltip: null,
      ticksValuesTooltip: null,
      vertical: false,
      getSelectionBarColor: null,
      getTickColor: null,
      getPointerColor: null,
      keyboardSupport: true,
      scale: 1,
      enforceStep: true,
      enforceRange: false,
      noSwitching: false,
      onlyBindHandles: false,
      onStart: null,
      onChange: null,
      onEnd: null,
      rightToLeft: false,
      boundPointerLabels: true,
      mergeRangeLabelsIfSame: false,
      customTemplateScope: null,
      logScale: false,
      customValueToPosition: null,
      customPositionToValue: null,
      selectionBarGradient: null
    };
    var globalOptions = {};

    var factory = {};
    factory.options = function(value) {
      angular.extend(globalOptions, value);
    };

    factory.getOptions = function(options) {
      return angular.extend({}, defaultOptions, globalOptions, options);
    };

    return factory;
  })

  .factory('rqThrottle', ['$timeout', function($timeout) {
    /**
     * rqThrottle
     *
     * Taken from underscore project
     *
     * @param {Function} func
     * @param {number} wait
     * @param {ThrottleOptions} options
     * @returns {Function}
     */
    return function(func, wait, options) {
      'use strict';
      /* istanbul ignore next */
      var getTime = (Date.now || function() {
        return new Date().getTime();
      });
      var context, args, result;
      var timeout = null;
      var previous = 0;
      options = options || {};
      var later = function() {
        previous = getTime();
        timeout = null;
        result = func.apply(context, args);
        context = args = null;
      };
      return function() {
        var now = getTime();
        var remaining = wait - (now - previous);
        context = this;
        args = arguments;
        if (remaining <= 0) {
          $timeout.cancel(timeout);
          timeout = null;
          previous = now;
          result = func.apply(context, args);
          context = args = null;
        } else if (!timeout && options.trailing !== false) {
          timeout = $timeout(later, remaining);
        }
        return result;
      };
    }
  }])

  .factory('RqSlieder', ['$timeout', '$document', '$window', '$compile', 'RqSliederOptions', 'rqThrottle', function($timeout, $document, $window, $compile, RqSliederOptions, rqThrottle) {
    'use strict';

    var Slieder = function(scope, sliederElem) {
      /**
       * The slieder's scope
       *
       * @type {ngScope}
       */
      this.scope = scope;

      /**
       * The slieder inner low value (linked to rqSliederModel)
       * @type {number}
       */
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
        rqSliederHigh: '=?',
        rqSliederOptions: '&?',
        rqSliederTplUrl: '@'
      },

      /**
       * Return template URL
       *
       * @param {jqLite} elem
       * @param {Object} attrs
       * @return {string}
       */
      templateUrl: 'js/modules/common/helppopup-template.html' ,

      link: function(scope, elem) {
        scope.slieder = new RqSlieder(scope, elem); //attach on scope so we can test it
      }
    };
  }]);

  return module.name
}));
