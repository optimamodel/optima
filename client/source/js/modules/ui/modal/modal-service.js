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
         *
         * Uses the custom message and title (if present) and
         * executes the right callback depending on the user's choice.
         */
        confirm: function (onAccepted, onRejected, acceptButton, rejectButton, message, title) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-confirm.html',
            controller: ['$scope', function ($scope) {
              $scope.title = title ? title : 'Please respond …';
              $scope.message = message || 'Are you sure?';
              $scope.acceptButton = acceptButton || 'Yes';
              $scope.rejectButton = rejectButton || 'No';
            }]
          }).result.then(onAccepted, onRejected);
        },

        /**
         * Displays the given message
         *
         * @param {function} onAccepted - callback for the acceptButton.
         * @param {string} onAccepted - text for the acceptButton.
         * @param {string} message - text for the description.
         * @param {string} title - text for the modal title.
         * @param {string} [errorText] - optional text for a error message.
         */
        inform: function (onAccepted, acceptButton, message, title, errorText) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-inform.html',
            controller: ['$scope', function ($scope) {
              $scope.message = message || 'Be informed';
              $scope.title = title || 'Attention...';
              $scope.acceptButton = acceptButton || 'Okay';
              $scope.errorText = errorText;
            }]
          }).result.finally(onAccepted);
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
        showPrompt: function (title, label, cb, options) {
          options = options || {};

          var modalInstance = $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-prompt.html',
            controller: ['$scope', function ($scope) {
              $scope.title = title;
              $scope.label = label;
              $scope.acceptButton = options.acceptButton || 'Yes';
              $scope.rejectButton = options.rejectButton || 'No';
              $scope.description = options.description || false;
              $scope.closeReason = options.closeReason || 'close';

              $scope.cb = function(enteredValue) {
                cb(enteredValue);
                modalInstance.close({ enteredValue: enteredValue });
              };
            }]
          });
        },

        /**
         * This function opens a modal that will ask the user to provide a name
         * for a new optimization.
         */
        addOptimization: function (callback, optimizations) {
          var modalInstance = $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-add-optimization.html',
            controller: ['$scope', function ($scope) {
              $scope.createOptimization = function (name) {
                callback(name);
                modalInstance.close();
              };

              $scope.isUniqueName = function (name, addOptimizationForm) {
                var exists = _(optimizations).some(function(item) {
                  return item.name == name;
                });
                addOptimizationForm.organizationName.$setValidity("organizationExists", !exists);
                return exists;
              };
            }]
          });

          return modalInstance;
        },

        /**
        * Asks the user to choose between two choices.
        *
        * Uses the custom message and title (if present) and executes the right
        * callback depending on the user's choice.
        */
        choice: function (onChoiceA, onChoiceB, choiceAButton, choiceBButton, message, title) {
          $modal.open({
            templateUrl: 'js/modules/ui/modal/modal-choice.html',
            controller: ['$scope', function ($scope) {
              $scope.title = title || '';
              $scope.message = message || '';
              $scope.choiceAButton = choiceAButton;
              $scope.choiceBButton = choiceBButton;

              $scope.chooseA = function() {
                onChoiceA();
                $scope.$close();
              };

              $scope.chooseB = function() {
                onChoiceB();
                $scope.$close();
              };
            }]
          });
        }

      };
    }]);
});
