define([
  'angular'
], function (angular) {

  'use strict';

  return angular.module('app.ui.spreadsheet-upload-hint', [])

  /**
   * <spreadsheet-upload-hint></spreadsheet-upload-hint>
   *
   * If the model data is missing this html snipped should be shown.
   */
    .directive('spreadsheetUploadHint', function () {
      return {
        restrict: 'E',
        templateUrl: 'js/modules/ui/spreadsheet-upload-hint/spreadsheet-upload-hint.html',
      };
    });

});
