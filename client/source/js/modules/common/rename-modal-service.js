/**
 * poller is a factory for tracking jobs on the server
 */

define(['angular' ], function (angular) {

  'use strict';

  return angular
    .module('app.rename-modal', [])
    .factory(
      'renameModalService', ['$modal', function($modal) {

      function openEditNameModal(
         acceptName, title, message, name, errorMessage, invalidNames) {

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/common/rename-modal.html',
          controller: [
            '$scope', '$document',
            function($scope, $document) {

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
                function() { $document.off('keydown', onKey); });

            }
          ]
        });

        return modalInstance;
      }

      return {
        openEditNameModal: openEditNameModal,
      };

    }]);


});
