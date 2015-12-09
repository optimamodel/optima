define(['angular', 'jquery'], function (module, $) {
  'use strict';

  return angular.module('app.common.update-checkbox-on-click', [])

  /**
   * Toggle the checkbox inside the clicked element.
   *
   * In order to avoid checking/unchecking with one click the toggle will
   * only be applied when the target is not the checkbox itselve.
   */
  .directive('updateCheckboxOnClick', [function () {
    return {
      link: function(scope, element, attrs, ctrl) {

        element.on('click', function(event) {
          // only toggle if the cell is clicked, but not the checkbox itselve
          // in order to prevent instanly reverting the action
          if (!$(event.target).is(':checkbox')) {
            // manually apply click directly on the checkbox
            $(event.currentTarget).find('input[type=checkbox]').click();
          }
        });
      }
    };
  }]);
});
