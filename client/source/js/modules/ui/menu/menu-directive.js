define(['jquery', 'underscore', './module'], function ($, _, module) {

  /**
   * <div data-menu="menuSettings" template="accordion"></div>
   *
   * {Object} menuSettings:
   *   - items
   *   - baseClass (for dropdown only)
   *
   * If template attribute is omitted "dropdown" will be used.
   * Other than that "accordion" can be used.
   */
  module.directive('menu', function ($state, $location) {
    return {
      restrict: 'A',
      scope: {
        settings: '= menu'
      },
      templateUrl: function(el, attrs) {
        var tmpl = attrs.template || 'dropdown';
        return 'js/modules/ui/menu/menu-' + tmpl + '.tpl.html';
      },
      link: function (scope, elem, attrs) {
        // no need to setup listeners below for non dropdown menus
        if (_.isString(attrs.template) && attrs.template.length && attrs.template !== 'dropdown') {
          return;
        }

        // open dropdowns on hover
        elem.on('mouseenter', '.dropdown', function () {
          $(this).addClass('open');
        });

        // hide dropdowns on hover
        elem.on('mouseleave', '.dropdown', function () {
          $(this).removeClass('open');
        });

        // hide dropdowns on click
        elem.on('click', function () {
          $(this).find('.dropdown').removeClass('open');
        });
      },
      controller: [
        '$scope',
        '$state',
        'typeSelector',
        function ($scope, $state, typeSelector) {
          // Single-level array of all menu items to easily find matches
          $scope._processedItems = [];

          $scope.types = typeSelector.types;

          $scope._processItems = function (items, parent) {

            _.each(items, function (item) {

              // Add current item to the resulting array
              // Should be done before diving into recursion
              // to keep proper order
              $scope._processedItems.push(item);

              // If there are subitems dive into next level of recursion
              // providing a reference to a parent item
              if (item.subitems) {
                return $scope._processItems(item.subitems, item);
              }

              if (parent) {
                item.parent = parent;
              }

              if (item.state) {
                var state = $state.get(item.state.name);

                if (!state) {
                  throw new Error('[ui-router] state "' + item.state.name + '" doest not exist');
                }

                // If there is a state provided get a reference to it
                item.url = item.state.name + '(' + (item.state.params ? JSON.stringify(item.state.params) : '{}') + ')';

              } else if (!item.click) {
                throw new Error('Menu accepts only states and clicks as targets for items.');
              }
            });
          };

          /**
           * Checks an item if they are active and stores their state
           * in a property
           *
           * @param {Object} toState
           * @returns {Function}
           * @private
           */
          $scope._getItemChecker = function (toState) {
            return function (item) {
              if (item.customHighlighting) {
                return;
              }

              if (item.matchingState) {
                item.active = (item.matchingState === toState.name.split('.')[0]);
              } else if (item.state) {
                item.active = (item.state.name === toState.name);
              } else if (item.url) {
                item.active = item.url === '#' + $location.url();
              } else {
                item.active = false;
              }

              if (item.active) {
                $scope.makeParentsActive(item);
              }
            };
          };

          /**
           * Recussively makes parents of current item active
           * @param {Object} item
           */
          $scope.makeParentsActive = function (item) {
            if (!item.parent) {
              return;
            }

            item.parent.active = true;
            $scope.makeParentsActive(item.parent);
          };

          $scope.checkItems = function (state) {
            _.each($scope._processedItems, $scope._getItemChecker(state));
          };

          $scope._processItems($scope.settings.items);
          $scope.checkItems($state.$current);

          $scope.$on('$stateChangeSuccess', function (event, toState) {
            $scope.checkItems(toState);
          });
        }
      ]
    };
  });
});
