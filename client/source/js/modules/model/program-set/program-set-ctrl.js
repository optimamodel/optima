define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    $timeout, modalService, predefined, availableParameters, UserManager, activeProject) {

    // Check if come project is currently open, else show error message
    const openProjectStr = activeProject.getProjectFor(UserManager.data);
    const openProject = openProjectStr ? JSON.parse(openProjectStr) : void 0;
    if(!openProject) {
      modalService.informError([{message: 'There is no project open currently.'}]);
    }

    // Initialize scope params
    $scope.activeProgramSet = {};
    $scope.categories = angular.copy(predefined.data.categories);
    $scope.programs = angular.copy(predefined.data.programs);
    $scope.programSetList = [];

    // Reset programs to defaults
    const resetPrograms = function() {
      $scope.programs = angular.copy(predefined.data.programs);
    };
    resetPrograms();

    // The function sets the current active program to the program passed
    $scope.setActiveProgramSet = function(program) {
      $scope.activeProgramSet = program;
      if (program.programs) {
        $scope.programs = program.programs;
      } else {
        resetPrograms();
      }
    };

    // Get the list of saved programs from DB and set the first one as active
    $http.get('/api/project/' + openProject.id + '/progsets' )
      .success(function (response) {
        if(response.progsets) {
          $scope.programSetList = response.progsets;
          if (response.progsets && response.progsets.length > 0) {
            $scope.setActiveProgramSet(response.progsets[0]);
          }
        }
      });

    // Open pop-up to add new programSet name, it will also reset programs
    $scope.addProgramSet = function () {
      var add = function (name) {
        const addedProgramSet = {name:name};
        $scope.programSetList[$scope.programSetList ? $scope.programSetList.length : 0] = addedProgramSet;
        $scope.setActiveProgramSet(addedProgramSet);
      };
      programSetModalService.openProgramSetModal(null, add, $scope.programSetList, 'Add program set', true);
    };

    // Open pop-up to edit progSet name
    $scope.editProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var edit = function (name) {
          $scope.activeProgramSet.name = name;
        };
        programSetModalService.openProgramSetModal($scope.activeProgramSet.name, edit, $scope.programSetList, 'Edit program set');
      }
    };

    // Delete a progSet from $scope.programSetList and also DB.
    $scope.deleteProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          if ($scope.activeProgramSet.id) {
            $http.delete('/api/project/' + openProject.id +  '/progsets' + '/' + $scope.activeProgramSet.id);
          }
          $scope.programSetList = _.filter($scope.programSetList, function (programSet) {
            return programSet.name !== $scope.activeProgramSet.name;
          });
          $scope.programSetList && $scope.programSetList.length > 0 ? $scope.setActiveProgramSet($scope.programSetList[0]) : void 0;
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
          const copiedProgramSet = {name: name, programs: $scope.activeProgramSet.programs};
          $scope.programSetList[$scope.programSetList.length] = copiedProgramSet;
          $scope.setActiveProgramSet(copiedProgramSet);
        };
        programSetModalService.openProgramSetModal($scope.activeProgramSet.name, copy, $scope.programSetList, 'Copy program set');
      }
    };

    // Save a programSet to DB
    $scope.saveProgramSet = function() {
      var errorMessage;
      if (!openProject) {
        errorMessage = 'Open project before proceeding.';
      } else if (!$scope.activeProgramSet || !$scope.activeProgramSet.name) {
        errorMessage = 'Please create a new program set before trying to save it.';
      }
      if (errorMessage) {
        modalService.informError([{message: errorMessage}]);
      } else {
        $http({
          url: '/api/project/' + openProject.id + '/progsets' + ($scope.activeProgramSet.id ? '/' + $scope.activeProgramSet.id : ''),
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
            'Project set saved successfully',
            'Project set saved'
          );
        });
      }
    };

    // Opens a modal for editing an existing program.
    $scope.openEditProgramModal = function ($event, program) {
      if ($event) {
        $event.preventDefault();
      }

      return programSetModalService.openProgramModal(program, predefined.data, availableParameters.data.parameters).result.then(
        function (newProgram) {
          _(program).extend(newProgram);
        }
      );
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

      return programSetModalService.openProgramModal(program, predefined.data, availableParameters.data.parameters).result.then(
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

      return programSetModalService.openProgramModal(program, predefined.data, availableParameters).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

  });
});
