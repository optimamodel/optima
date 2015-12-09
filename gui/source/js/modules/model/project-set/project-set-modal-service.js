/**
 *  A service with helper functions for calibration.
 */
define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('projectSetModalService', ['$modal', function ($modal) {

    return {

      /**
       * This function opens a modal that will ask the user to provide a name
       * for a new projectSet.
       */
      addProjectSet: function (callback, projectSetList) {

        var onModalKeyDown = function (event) {
          if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/model/project-set/modal-add-project-set.html',
          controller: ['$scope', '$document', function ($scope, $document) {

            $scope.createProjectSet = function (name) {
              $scope.addedProjectSetName = name;
              callback(name);
              modalInstance.close();
            };

            $scope.isUniqueName = function (name, addProjectSetForm) {
              var exists = _(projectSetList).some(function(item) {
                    return item.name == name;
                  }) && name !== $scope.addedProjectSetName;
              addProjectSetForm.projectSetName.$setValidity("projectSetListExists", !exists);
              return exists;
            };

            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function (){ $document.off('keydown', onModalKeyDown); });  // unobserve

          }]
        });

        return modalInstance;
      },

      /**
       * This function opens a modal that will ask the user to provide a name
       * to edit an existing projectSet.
       */
      editProjectSet: function (projectSetName, callback, projectSetList, title) {

        var onModalKeyDown = function (event) {
          if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/model/project-set/modal-edit-project-set.html',
          controller: ['$scope', '$document', function ($scope, $document) {

            $scope.title = title || 'Edit ProjectSet';

            $scope.name = projectSetName;

            $scope.updateProjectSet = function (name) {
              $scope.updatedProjectSetName = name;
              callback(name);
              modalInstance.close();
            };

            $scope.isUniqueName = function (name, editProjectSetForm) {
              var exists = _(projectSetList).some(function(item) {
                    return item.name == name;
                  }) && name !== projectSetName && name !== $scope.updatedProjectSetName;
              editProjectSetForm.projectSetName.$setValidity("projectSetListExists", !exists);
              editProjectSetForm.projectSetName.$setValidity("projectSetListUpdated", name !== projectSetName);
              return exists;
            };

            $document.on('keydown', onModalKeyDown); // observe
            $scope.$on('$destroy', function (){ $document.off('keydown', onModalKeyDown); });  // unobserve

          }]
        });

        return modalInstance;
      },

      /**
       * This function opens a modal that will ask the user to provide a new name
       * for the copied projectSet.
       */
      copyProjectSet: function (projectSetName, callback, projectSetList) {
        this.editProjectSet(projectSetName, callback, projectSetList, 'Copy ProjectSet');
      }

    };
  }]);
});
