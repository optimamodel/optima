/**
 * ConfirmModalController has the model and behavior of a generic confirm/cancel type of dialog.s
 * It evaluates the custom callback regarding to user's choice.
 */

define(['./module'], function (module) {
  'use strict';

  module.controller('ConfirmModalController', function ($scope, $modalInstance, $event) {
    debugger
    var initialize = function() {
      console.log('ConfirmModalController.initialize()');
    };

    /*
     * Closes the dialog executing the confirm callback
     */
    var confirm = function ($event) {
      console.log( 'confirm clicked');
      if ($event) { $event.preventDefault(); }
      // $modalInstance.close();
      $dismiss('Closed');
      return $modalInstance.model.onConfirm();
    };

    /*
     * Closes the dialog executing the cancel callback
     */
    var cancel = function ($event) {
      console.log( 'cancel clicked');
      if ($event) { $event.preventDefault(); }
      $dismiss('Closed');
      // $modalInstance.close();
      return $modalInstance.model.onCancel();
    };

    initialize();

  });

});
