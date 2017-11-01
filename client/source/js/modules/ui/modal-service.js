/**
 * modalService provides controllers of a set of reusable modals.
 * They can display custom messages and title and action callbacks.
 */
define(['angular', 'ui.bootstrap'], function(angular) {

  'use strict';

  var module = angular.module('app.modal', ['ui.bootstrap']);

  module.factory('modalService', ['$modal', function($modal) {

    return {

      confirm: function(onAccepted, onRejected, acceptButton, rejectButton, message, title) {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 78) {
            return modalInstance.dismiss('N');
          } // N
          if (event.keyCode == 89) {
            return modalInstance.close('Y');
          } // Y
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-confirm.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $scope.title = title ? title : 'Please respond …';
            $scope.message = message || 'Are you sure?';
            $scope.acceptButton = acceptButton || 'Yes';
            $scope.rejectButton = rejectButton || 'No';
            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve
          }]
        });
        return modalInstance.result.then(onAccepted, onRejected);
      },

      /**
       * @param {function} onAccepted - callback for the acceptButton.
       * @param {string} onAccepted - text for the acceptButton.
       * @param {string} message - text for the description.
       * @param {string} title - text for the modal title.
       * @param {string} [errorText] - optional text for a error message.
       */
      inform: function(onAccepted, acceptButton, message, title, errorText) {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 79) {
            return modalInstance.dismiss('O');
          } // O of OK
          if (event.keyCode == 13) {
            return modalInstance.close('ENTER');
          }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-inform.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $scope.message = message || 'Be informed';
            $scope.title = title || 'Attention...';
            $scope.acceptButton = acceptButton || 'Okay';
            $scope.errorText = errorText;
            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve
          }]
        });
        return modalInstance.result.finally(onAccepted);
      },

      /**
       * Opens a modal that will display the `errors` object.
       * It parses errors to display them neatly to the user.
       */
      informError: function(errors, title) {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 79) {
            return modalInstance.dismiss('O');
          } // O of OK
          if (event.keyCode == 13) {
            return modalInstance.close('ENTER');
          }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-inform-errors.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $scope.errors = errors;
            $scope.title = title ? title : 'Error';
            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve
          }]
        });
        return modalInstance;
      },
	  
      /**
       * Opens a modal that displays the Optima Lite projects that are 
	   * available to the user.
       */
      optimaLiteProjectList: function() {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 79) {
            return modalInstance.dismiss('O');
          } // O of OK
          if (event.keyCode == 13) {
            return modalInstance.close('ENTER');
          }
        };

        var modalInstance = $modal.open({
		  templateUrl: 'js/modules/ui/modal-optimalite.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve
          }]
        });
        return modalInstance;
      },
	  
      /**
       * Opens a modal that displays the Optima Terms and Conditions for 
	   * user registration.
       */	  
      termsAndConditions: function() {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 79) {
            return modalInstance.dismiss('O');
          } // O of OK
          if (event.keyCode == 13) {
            return modalInstance.close('ENTER');
          }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-termsconditions.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve
          }]
        });
        return modalInstance;
      },
	  
      /**
       * This function opens a modal that will ask user to enter a value.
       */
      showPrompt: function(title, label, cb, options) {

        var onModalKeyDown = function(event) {
          if (event.keyCode == 27) {
            return modalInstance.dismiss('ESC');
          }
        };

        options = options || {};

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-prompt.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
            $scope.title = title;
            $scope.label = label;
            $scope.acceptButton = options.acceptButton || 'Yes';
            $scope.rejectButton = options.rejectButton || 'No';
            $scope.description = options.description || false;
            $scope.closeReason = options.closeReason || 'close';

            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve

            $scope.cb = function(enteredValue) {
              cb(enteredValue);
              modalInstance.close({enteredValue: enteredValue});
            };
          }]
        });
      },

      /**
       * Asks the user to choose between two choices.
       *
       * Uses the custom message and title (if present) and executes the right
       * callback depending on the user's choice.
       */
      choice: function(onChoiceA, onChoiceB, choiceAButton, choiceBButton, message, title) {
        var onModalKeyDown = function(event) {
          if (event.keyCode == 27) {
            return modalInstance.dismiss('ESC');
          }
        };
        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-choice.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {
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

            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function() {
              $document.off('keydown', onModalKeyDown);
            });  // unobserve

          }]
        });
        return modalInstance;
      },

      /**
       * Asks the user to create/edit a name for
       *
       * Uses the custom message and title (if present) and invalidates the input
       *  if it matches any of the invalidNames.
       */
      rename: function(acceptName, title, message, name, errorMessage, invalidNames) {

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/ui/modal-rename.html?cacheBust=xxx',
          controller: ['$scope', '$document', function($scope, $document) {

            $scope.name = name;
            $scope.title = title;
            $scope.message = message;
            $scope.errorMessage = errorMessage;

            $scope.checkBadForm = function(form) {
              var isGoodName = !_.contains(invalidNames, $scope.name);
              form.$setValidity("name", isGoodName);
              return !isGoodName;
            };

            $scope.submit = function() {
              acceptName($scope.name);
              modalInstance.close();
            };

            function onKey(event) {
              if (event.keyCode == 27) {
                return modalInstance.dismiss('ESC');
              }
            }

            $document.on('keydown', onKey);
            $scope.$on(
              '$destroy',
              function() {
                $document.off('keydown', onKey);
              });

          }
          ]
        });

        return modalInstance;
      }

    };
  }]);
});
