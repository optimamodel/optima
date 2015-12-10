define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.factory('programSetModalService', ['$modal', function ($modal) {

    /*
     * Returns a collection of entries where all non-active antries are filtered
     * out and the active attribute is removed from each of these entries.
     */
    var toCleanArray = function (collection) {
      return _(collection).chain()
        .where({ active: true })
        .map(function (item) {
          var cl = _(item).omit(['active', '$$hashKey']);
          if (cl.parameters) {
            cl.parameters = _(cl.parameters).chain()
              .where({ active: true })
              .map(function (param) {
                return _(param).omit(['active', '$$hashKey']);
              })
              .value();
            if (cl.parameters === 0) delete cl.parameters;
          }
          return cl;
        })
        .value();
    };

    return {

      /**
       * This function opens a modal that will ask the user to provide a name
       * for a new projectSet.
       */
      addProjectSet: function (callback, projectSetList) {
        this.editProjectSet(undefined, callback, projectSetList, 'Add program set');
      },

      /**
       * This function opens a modal that will ask the user to provide a name
       * to edit an existing projectSet.
       */
      editProjectSet: function (projectSetName, callback, projectSetList, title, isEdit) {

        var onModalKeyDown = function (event) {
          if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
        };

        var modalInstance = $modal.open({
          templateUrl: 'js/modules/model/program-set/program-set-modal.html',
          controller: ['$scope', '$document', function ($scope, $document) {

            $scope.isEdit = true;

            $scope.title = title;

            $scope.name = projectSetName;

            $scope.updateProjectSet = function (name) {
              $scope.newProjectSetName = name;
              callback(name);
              modalInstance.close();
            };

            $scope.isUniqueName = function (name, editProjectSetForm) {
              var exists = _(projectSetList).some(function(item) {
                    return item.name == name;
                  }) && name !== projectSetName && name !== $scope.newProjectSetName;
              editProjectSetForm.projectSetName.$setValidity("projectSetListExists", !exists);
              isEdit && editProjectSetForm.projectSetName.$setValidity("projectSetListUpdated", name !== projectSetName);
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
       * for copying projectSet.
       */
      copyProjectSet: function (projectSetName, callback, projectSetList) {
        this.editProjectSet(projectSetName, callback, projectSetList, 'Copy ProjectSet');
      },

      openProgramModal: function (program, predefined, availableParameters) {
        return $modal.open({
          templateUrl: 'js/modules/model/program-set/program-modal.html',
          controller: 'ProgramSetModalController',
          size: 'lg',
          resolve: {
            program: function () {
              return program;
            },
            availableParameters: function () {
              return availableParameters;
            },
            populations: function () {
              return toCleanArray(predefined.categories);
            }
          }
        });
      }

  };
  }]);
});
