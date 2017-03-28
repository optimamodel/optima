/**
 * modalService provides controllers of a set of reusable modals.
 * They can display custom messages and title and action callbacks.
 */
define(['angular', 'ui.bootstrap'], function(angular) {

  'use strict';

  var module = angular.module('app.ui.modal', ['ui.bootstrap']);

  /**
   * directive validate-with="regular expression" - will parse
   * for regular expressions on key-resses and reset if the
   * regular-expression has failed
   */
  module.directive('validateWith', function() {
    return {
      require: 'ngModel',
      link: function(scope, element, attrs, ctrl) {
        var regexp = eval(attrs.validateWith);
        var origVal;
        // store the current value as it was before the change was made
        element.on("keypress", function(e) {
          origVal = element.val();
        });

        ctrl.$parsers.push(function(val) {
          if (val == "") {
            return val;
          }
          var valid = regexp.test(val);
          console.log('parse-regex regex', valid, val, origVal);
          console.log('parse-regex attrs name', attrs['name']);
          console.log('parse-regex $invalid', scope[attrs['name']]);
          if (!valid) {
            ctrl.$setViewValue(origVal);
            ctrl.$render();
            return origVal;
          }
          return val;
        });
      }
    }
  })

  /**
   * directive my-enter="callbackfn()" to catch <input> elements
   * for enter key presses
   */
  module.directive('myEnter', function() {
    return function(scope, element, attrs) {
      element.bind("keydown keypress", function(event) {
        if (event.which === 13) {
          scope.$apply(function() {
            scope.$eval(attrs.myEnter);
          });

          event.preventDefault();
        }
      });
    };
  })

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
          templateUrl: 'js/modules/ui/modal-confirm.html',
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
          templateUrl: 'js/modules/ui/modal-inform.html',
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
          templateUrl: 'js/modules/ui/modal-inform-errors.html',
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
          templateUrl: 'js/modules/ui/modal-prompt.html',
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
          templateUrl: 'js/modules/ui/modal-choice.html',
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
          templateUrl: 'js/modules/ui/modal-rename.html',
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
      },

      getUniqueName: function(name, otherNames) {
        var i = 0;
        var uniqueName = name;
        while (_.indexOf(otherNames, uniqueName) >= 0) {
          i += 1;
          uniqueName = name + ' (' + i + ')';
        }
        return uniqueName;
      }

    };
  }]);
});
