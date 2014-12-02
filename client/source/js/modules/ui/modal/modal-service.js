/**
 * modalService provides controllers of a set of reusable modals. 
 * They can display custom messages and title and action callbacks.
 */
define([
  'angular',
  'ui.bootstrap'
], function (angular) {
  'use strict';

  return angular.module('app.ui.modal', [
    'ui.bootstrap'
  ])
    .factory('modalService', ['$modal', function ($modal) {
      return {

        /**
         * Asks the user for confirmation.
         * Uses the custom message and title (if present) and
         * executes the right callback depending on the user's choice.
         */
        confirm: function (onAccepted, onRejected, acceptButton, rejectButton, message, title) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-confirm.html',
            controller: ['$scope', function ($scope) {
              $scope.title = title ? title : 'Please respond...';
              $scope.message = message || 'Are you sure?';
              $scope.acceptButton = acceptButton || 'Yes';
              $scope.rejectButton = rejectButton || 'No';
            }]
          }).result.then(onAccepted, onRejected);
        },

        /**
         * Displays the given message and uses the title in the modal header
         */
        inform: function (onAccepted, message, title) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-inform.html',
            controller: ['$scope', function ($scope) {
              $scope.message = message || 'Be informed';
              $scope.title = title || 'Attention...';
            }]
          }).then(onAccepted);
        },

        /**
         * Opens a modal that will display the `errors` object.  
         * It parses errors to display them neatly to the user.
         */
        informError: function (errors, title) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-inform-errors.html',
            controller: ['$scope', function ($scope) {
              $scope.errors = errors;
              $scope.title = title ? title : 'Error';
            }]
          });
        },

        /**
         * This function opens a modal that will ask user to enter a value.
         */
        showPrompt: function (title, label, cb) {
          var modalInstance = $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-prompt.html',
            controller: ['$scope', function ($scope) {
              $scope.title = title;
              $scope.label = label;

              $scope.cb = function(enteredValue) {
                cb(enteredValue);
                modalInstance.close({ enteredValue: enteredValue });
              };
            }]
          });
        }

      };
    }]);
});
