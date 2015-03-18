define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('TypeSelectorController', function ($scope, $state, typeSelector, CONFIG) {

      $scope.state = {};
      $scope.types = typeSelector.types;

      /**
       * @description Adds a parameter on scope that will indicate if something should be visible depending on the current state
       * @param part name of the parameter that should be set on $scope
       * @param viewNames names of the views in which this parameter should return true
       */
      function showPartInViews (part, viewNames) {
        $scope.state[part+"IsVisible"] = _(viewNames).contains($state.current.name);
      }

      $scope.$on('$stateChangeSuccess',function() {
        var allPagesWithSelector = [
          'model.view',
          'analysis.scenarios',
          'analysis.optimization'
        ];
        var analysisPages = [
          'analysis.scenarios',
          'analysis.optimization'
        ];
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

        showPartInViews('typeSelector', allPagesWithSelector);

        showPartInViews('stackedCheckbox',[
          'model.view'
        ]);

        showPartInViews('plotUncertainties',[
          'analysis.optimization'
        ]);
      });
    }
  );
});
