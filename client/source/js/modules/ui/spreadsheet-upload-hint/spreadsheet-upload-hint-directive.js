define(['./module'], function (module) {

  /**
   * <spreadsheet-upload-hint></spreadsheet-upload-hint>
   *
   * If the model data is missing this html snipped should be shown.
   */
  module.directive('spreadsheetUploadHint', function () {
    return {
      restrict: 'E',
      templateUrl: 'js/modules/ui/spreadsheet-upload-hint/spreadsheet-upload-hint.html',
    };
  });
});
