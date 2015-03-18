define([
  'angular', '../../../config'
  ], function (angular) {
    'use strict';

    return angular.module('app.ui.type-selector', ['app.constants'])
      .directive('typeSelector', function() {
        return {
          replace: true,
          restrict: 'E',
          templateUrl: 'js/modules/ui/type-selector/type-selector.html',
          controller: 'TypeSelectorController'
        };
    });
  });
