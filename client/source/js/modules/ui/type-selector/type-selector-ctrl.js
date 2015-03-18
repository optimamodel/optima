define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('TypeSelectorController', function ($scope, $state) {

      $scope.state = {};

      /**
       * @description Adds a parameter on scope that will indicate if something should be visible depending on the current state
       * @param part name of the parameter that should be set on $scope
       * @param viewNames names of the views in which this parameter should return true
       */
      function showPartInViews (part, viewNames) {
        $scope.state[part+"IsVisible"] = _(viewNames).contains($state.current.name);
      }

      $scope.$on('$stateChangeSuccess',function() {
        showPartInViews('typeSelector', [
          'model.view',
          'analysis.scenarios',
          'analysis.optimization'
        ]);

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
