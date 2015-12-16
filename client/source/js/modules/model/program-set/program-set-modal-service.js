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
