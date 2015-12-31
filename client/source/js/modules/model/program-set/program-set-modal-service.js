define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('programSetModalService', ['$modal', function ($modal) {

    return {

      /**
       * This function opens a modal for creating, editing and copying a programSet.
       */
      openProgramSetModal: function (programSetName, callback, programSetList, title, isAdd) {

        var onModalKeyDown = function (event) {
          if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/model/program-set/program-set-modal.html',
          controller: ['$scope', '$document', function ($scope, $document) {

            $scope.isEdit = true;

            $scope.title = title;

            $scope.name = programSetName;

            $scope.updateProgramSet = function (name) {
              $scope.newProgramSetName = name;
              callback(name);
              modalInstance.close();
            };

            $scope.isUniqueName = function (name, editProgramSetForm) {
              var exists = _(programSetList).some(function(item) {
                    return item.name == name;
                  }) && name !== programSetName && name !== $scope.newProgramSetName;
              editProgramSetForm.programSetName.$setValidity("programSetListExists", !exists);
              !isAdd && editProgramSetForm.programSetName.$setValidity("programSetListUpdated", name !== programSetName);
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
      openProgramModal: function (program, populations, availableParameters, programList) {
        return $modal.open({
          templateUrl: 'js/modules/model/program-set/program-modal.html',
          controller: 'ProgramSetModalController',
          size: 'lg',
          resolve: {
            program: function () {
              return program;
            },
            programList: function () {
              return programList;
            },
            availableParameters: function () {
              return availableParameters;
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
