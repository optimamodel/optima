define(['./module', 'underscore'], function (module, _) {
  'use strict';

  /**
   * The controller manages the avialable & selected chart types.
   *
   * Different type selection sections are shown depending the current page.
   * This controller manages the types selection made available through the
   * typeSelector service to use in the page specific controllers.
   */
  module.controller('TypeSelectorController', function ($scope, $state, typeSelector, CONFIG) {

      function initialize () {
        $scope.state = {};
        $scope.types = typeSelector.types;
        $scope.$on('$stateChangeSuccess', onStateChanged);
      }

      /**
       * Reset the types and update the visible sections when a user changes the page.
       */
      function onStateChanged () {
        var allPagesWithSelector = [
          'model.view',
          'analysis.scenarios',
          'analysis.optimization'
        ];
        var analysisPages = [
          'analysis.scenarios',
          'analysis.optimization'
        ];

        // reset the graph types
        if (_(allPagesWithSelector).contains($state.current.name)) {
          angular.extend($scope.types, angular.copy(CONFIG.GRAPH_TYPES));

          // for pages without stacked charts overall charts are set by default
          if (_(analysisPages).contains($state.current.name)) {
            var stackedTypes = ['plhiv', 'daly', 'death', 'inci', 'dx'];
            $scope.types.population = _($scope.types.population).map(function(type) {
              if (_(stackedTypes).contains(type.id)) {
                type.stacked = false;
                type.total = true;
              }
              return type;
            });
          }
        }

        // update section visibility
        updateVisibilityOf('typeSelector', allPagesWithSelector);
        updateVisibilityOf('stackedCheckbox', ['model.view']);
        updateVisibilityOf('plotUncertainties', ['analysis.optimization']);
      }

      /**
       * Adds a parameter on scope that will indicate if this section should be
       * visible depending on the current state.
       *
       * @param {string} section - name of the parameter that should be set on $scope
       * @param {array} viewNames - names of the views in which this parameter should return true
       */
      function updateVisibilityOf (section, viewNames) {
        $scope.state[section + "IsVisible"] = _(viewNames).contains($state.current.name);
      }

      initialize();
    }
  );
});
