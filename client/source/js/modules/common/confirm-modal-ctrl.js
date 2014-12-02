/**
 * ConfirmModalController has the view and behavior of generic confirm/cancel type of dialog.s
 */

define(['./module'], function (module) {
  'use strict';

  module.controller('ConfirmModalController', function ($scope, $modalInstance, $event) {

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
      return $scope.model.onConfirm();
    };

    /*
     * Closes the dialog executing the cancel callback
     */
    var cancel = function ($event) {
      console.log( 'cancel clicked');
      if ($event) { $event.preventDefault(); }
      $dismiss('Closed');
      // $modalInstance.close();
      return $scope.model.onCancel();
    };

    initialize();

  });

});
