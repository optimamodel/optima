define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    modalService, currentProject, projectApiService) {

    var openProjectData = currentProject.data;
    var defaults;

    if (!openProjectData.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $scope.missingData = true;
      return;
    }

    // Get the list of saved programs from DB and set the first one as active
    $http.get('/api/project/' + openProjectData.id + '/progsets' )
      .success(function (response) {
        if(response.progsets) {
          $scope.programSetList = response.progsets;
          if (response.progsets && response.progsets.length > 0) {
            $scope.setActiveProgramSet(response.progsets[0]);
          }
        }
      });

    projectApiService.getDefault(openProjectData.id)
      .success(function (response) {
        defaults = response;
        $scope.categories = angular.copy(response.categories);
      });

    // The function sets the current active program to the program passed
    $scope.setActiveProgramSet = function(programSet) {
      $scope.activeProgramSet = programSet;
    };

    // Open pop-up to add new programSet name, it will also reset programs
    $scope.addProgramSet = function () {
      var add = function (name) {
        var addedProgramSet = {name:name, programs: angular.copy(defaults.programs)};
        $scope.programSetList[$scope.programSetList ? $scope.programSetList.length : 0] = addedProgramSet;
        $scope.setActiveProgramSet(addedProgramSet);
      };
      programSetModalService.openProgramSetModal(null, add, $scope.programSetList, 'Add program set');
    };

    // Open pop-up to edit progSet name
    $scope.renameProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var edit = function (name) {
          $scope.activeProgramSet.name = name;
        };
        programSetModalService.openProgramSetModal($scope.activeProgramSet.name, edit, $scope.programSetList, 'Edit program set', true);
      }
    };

    // Delete a progSet from $scope.programSetList and also DB.
    $scope.deleteProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          if ($scope.activeProgramSet.id) {
            $http.delete('/api/project/' + openProjectData.id +  '/progsets' + '/' + $scope.activeProgramSet.id).
              success(function() {
                $scope.programSetList = _.filter($scope.programSetList, function (programSet) {
                  return programSet.name !== $scope.activeProgramSet.name;
                });
                $scope.programSetList && $scope.programSetList.length > 0 ? $scope.setActiveProgramSet($scope.programSetList[0]) : void 0;
              });
          }
        };
        modalService.confirm(
          function () {
            remove()
          }, function () {
          }, 'Yes, remove this program set', 'No',
          'Are you sure you want to permanently remove program set "' + $scope.activeProgramSet.name + '"?',
          'Delete program set'
        );
      }
    };

    // Copy a progSet
    $scope.copyProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var copy = function (name) {
          var copiedProgramSet = {name: name, programs: $scope.activeProgramSet.programs};
          $scope.programSetList[$scope.programSetList.length] = copiedProgramSet;
          $scope.setActiveProgramSet(copiedProgramSet);
        };
        programSetModalService.openProgramSetModal($scope.activeProgramSet.name + ' copy', copy, $scope.programSetList, 'Copy program set');
      }
    };

    // Save a programSet to DB
    $scope.saveProgramSet = function() {
      var errorMessage;
      if (!$scope.activeProgramSet || !$scope.activeProgramSet.name) {
        errorMessage = 'Please create a new program set before trying to save it.';
      }
      if (errorMessage) {
        modalService.informError([{message: errorMessage}]);
      } else {
        $http({
          url: '/api/project/' + openProjectData.id + '/progsets' + ($scope.activeProgramSet.id ? '/' + $scope.activeProgramSet.id : ''),
          method: ($scope.activeProgramSet.id ? 'PUT' : 'POST'),
          data: {
            name: $scope.activeProgramSet.name,
            programs: $scope.programs
          }
        }).success(function (response) {
          if(response.id) {
            $scope.activeProgramSet.id = response.id;
          }
          modalService.inform(
            function (){},
            'Okay',
            'Program set saved successfully',
            'Program set saved'
          );
        });
      }
    };

    // Opens a modal for editing an existing program.
    $scope.openEditProgramModal = function ($event, program) {
      return programSetModalService.openProgramModal(program, openProjectData.populations, null, $scope.programs);
    };

    /*
     * Creates a new program and opens a modal for editing.
     *
     * The entry is only pushed to the list of programs if editing in the modal
     * ended with a successful save.
     */
    $scope.openAddProgramModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var program = {};

      return programSetModalService.openProgramModal(program, openProjectData.populations, null, $scope.programs).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

    /*
     * Makes a copy of an existing program and opens a modal for editing.
     *
     * The entry is only pushed to the list of programs if editing in the modal
     * ended with a successful save.
     */
    $scope.copyProgram = function ($event, existingProgram) {
      if ($event) {
        $event.preventDefault();
      }
      var program = angular.copy(existingProgram);
      program.name = program.name + ' copy';
      program.short_name = program.short_name + ' copy';

      return programSetModalService.openProgramModal(program, openProjectData.populations, null, $scope.programs).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

  });
});
