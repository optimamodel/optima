define([
  'angular'
  ], function (angular) {
    'use strict';

    return angular.module('app.ui.type-selector', [])
      .directive('typeSelector', function() {
        return {
          replace: true,
          restrict: 'E',
          templateUrl: 'js/modules/ui/type-selector/type-selector.html',
          controller: 'TypeSelectorController',
          scope: {
            types: '='
          }
        };
    });
  });
