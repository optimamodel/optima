define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('programSetModalService', ['$modal', function ($modal) {

    return {

      /**
       * This function opens a modal for creating, editing and copying a programSet.
       */
      openProgramSetModal: function (callback, title, programSetList, programSetName, operation, isRename) {

        var onModalKeyDown = function (event) {
          if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/project-set/program-set/program-set-modal.html',
          controller: ['$scope', '$document', function ($scope, $document) {

            $scope.title = title;
            $scope.name = programSetName;
            $scope.operation = operation;

            $scope.updateProgramSet = function () {
              $scope.newProgramSetName = $scope.name;
              callback($scope.name);
              modalInstance.close();
            };

            $scope.isUniqueName = function (programSetForm) {
              var exists = _(programSetList).some(function(item) {
                    return item.name == $scope.name;
                  }) && $scope.name !== programSetName && $scope.name !== $scope.newProgramSetName;

              if(isRename) {
                programSetForm.programSetName.$setValidity("programSetUpdated", $scope.name !== programSetName);
              }
              programSetForm.programSetName.$setValidity("programSetExists", !exists);

              return exists;
            };

            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function (){ $document.off('keydown', onModalKeyDown); });  // unobserve

          }]
        });

        return modalInstance;
      },

      /**
       * This function opens a modal for creating, editing and copying a program.
       */
      openProgramModal: function (program, populations, programList) {
        return $modal.open({
          templateUrl: 'js/modules/project-set/program-set/program-modal.html',
          controller: 'ProgramSetModalController',
          size: 'lg',
          resolve: {
            program: function () {
              return program;
            },
            programList: function () {
              return programList;
            },
            populations: function () {
              return populations;
            }
          }
        });
      }

  };
  }]);
});
