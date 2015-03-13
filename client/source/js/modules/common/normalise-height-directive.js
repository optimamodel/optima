/**
* This directive triggers 'onAfterRender' once it's redered.
* Also can evaluate arbitrary code for people that know what they are doing
* Do not abuse the expression evaluator by making the view do things the controller should do!
*/

// normalizing-tallest-heigh
// normalize-height


define(['angular', 'jquery', 'underscore'], function (angular, $, _) {
  'use strict';

  return angular.module('app.common.normalise-height', [])
    .directive('normaliseHeight', function(normalisingHeightStore) {
      var def = {
        restrict : 'A',
        terminal : true,
        transclude : false,
        link : function(scope, element, attrs) {
          normalisingHeightStore.registerElement(element);

          scope.$on("$destroy", function() {
            normalisingHeightStore.unregisterElement(element);
          });
        }
      };
      return def;
    })
    .factory('normalisingHeightStore', function() {
      var maxHeight = 0;
      var elements = [];

      /**
       * Returns the max height of all existing elements.
       *
       * In case the list is empty 0 is returned.
       */
      var _maxHeightOfElement = function () {
        if (_.isEmpty(elements)) {
          return 0;
        } else {
          return _.max(elements, function (element) {
            return element.height();
          }).height();
        }
      };

      /**
       * Iterates over all elements & applies the new height.
       */
      var _normalizeElements = function () {
        _(elements).each(function(element) {
          element.height(maxHeight);
        });
      };

      /**
       * Registers an element to be taken into account for normalising the
       * height of all these elements.
       *
       * Important: Any element which re-draws itself & changes the height
       * during this process must trigger a jQuery `draw` event for the new
       * height to be taken into account.
       */
      var registerElement = function (element) {

        /**
         * Normalizes the necessary elements, but tries to leverage the cached
         * maxHeight to do as little manipualtion as possible.
         */
        var update = function(newHeight) {
          if (newHeight > maxHeight) {
            maxHeight = newHeight;
            _normalizeElements();
          } else if (newHeight < maxHeight) {
            // In case the element was the largerest & shrinked a new max height
            // must be determinant
            var newMaxHeight = _maxHeightOfElement();
            if (newMaxHeight < maxHeight) {
              maxHeight = newMaxHeight;
              _normalizeElements();
            } else {
              element.height(maxHeight);
            }
          }
        };

        elements.push(element);
        element.on('draw', function(event, dimensions) {
          update(dimensions.height);
        });
        update(element.height());
      };

      /**
       * Removes an element from the list of influencing the maximum height for
       * normalising all the height values.
       *
       * Usually this would be called once an element is removed from the DOM.
       */
      var unregisterElement = function(element) {
        element.off( "draw", "**" );
        elements = _(elements).filter(function(el) { return !el.is(element); });
        if (element.height() == maxHeight) {
          // since the new normalized height might be smaller the max height of
          // all remaining elements must be retrieved
          var newMaxHeight = _maxHeightOfElement();
          if (newMaxHeight < maxHeight) {
            maxHeight = newMaxHeight;
            _normalizeElements();
          }
        }
      };

      return {
        registerElement: registerElement,
        unregisterElement: unregisterElement
      };
    });
});
