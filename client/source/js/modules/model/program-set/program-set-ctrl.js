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

    // Initialize state
    $scope.state = {
      activeProgramSet: {},
      categories: predefined.categories,
      programs: predefined.programs
    };

    // Reset programs to defaults
    const resetPrograms = function() {
      $scope.state.programs = predefined.programs;
    };
    resetPrograms();

    // The function sets the current active program to the program passed
    $scope.setActiveProgramSet = function(program) {
      $scope.state.activeProgramSet = program;
      if (program.programs) {
        $scope.state.programs = program.programs;
      } else {
        resetPrograms();
      }
    };

    // Get the list of saved programs from DB and set the first one as active
    $http({
      url: '/api/project/progsets/' + openProject.id,
      method: 'GET'})
      .success(function (response) {
        $scope.state.programSetList = response.progsets || [];
        if(response.progsets && response.progsets.length > 0) {
          $scope.setActiveProgramSet(response.progsets[0]);
        }
      });

    // Open pop-up to add new programSet name, it will also reset programs
    $scope.addProgramSet = function () {
      var add = function (name) {
        const addedProgramSet = {name:name};
        $scope.state.programSetList[$scope.state.programSetList.length] = addedProgramSet;
        $scope.setActiveProgramSet(addedProgramSet);
      };
      programSetModalService.openProgramSetModal(null, add, $scope.state.programSetList, 'Add program set', true);
    };

    // Open pop-up to edit progSet name
    $scope.editProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var edit = function (name) {
          $scope.state.activeProgramSet.name = name;
        };
        programSetModalService.openProgramSetModal($scope.state.activeProgramSet.name, edit, $scope.state.programSetList, 'Edit program set');
      }
    };

    // Delete a progSet from $scope.state.programSetList and also DB.
    $scope.deleteProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          if ($scope.state.activeProgramSet.id) {
            $http({
              url: 'api/project/progsets/' + openProject.id + '/' + $scope.state.activeProgramSet.id,
              method: 'DELETE'
            });
          }
          $scope.state.programSetList = _.filter($scope.state.programSetList, function (programSet) {
            return programSet.name !== $scope.state.activeProgramSet.name;
          });
          $scope.state.programSetList ? $scope.setActiveProgramSet($scope.state.programSetList[0]) : void 0;
        };
        modalService.confirm(
          function () {
            remove()
          }, function () {
          }, 'Yes, remove this program set', 'No',
          'Are you sure you want to permanently remove program set "' + $scope.state.activeProgramSet.name + '"?',
          'Delete program set'
        );
      }
    };

    // Copy a progSet
    $scope.copyProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var copy = function (name) {
          const copiedProgramSet = {name: name};
          $scope.state.programSetList[$scope.state.programSetList.length] = copiedProgramSet;
          $scope.setActiveProgramSet(copiedProgramSet);
        };
        programSetModalService.openProgramSetModal($scope.state.activeProgramSet.name, copy, $scope.state.programSetList, 'Copy program set');
      }
    };

    // Save a programSet to DB
    $scope.saveProgramSet = function() {
      if (!openProject) {
        modalService.informError([{message: 'Open project before proceeding.'}]);
      } else {
        $http({
          url: 'api/project/progsets/' + openProject.id + ($scope.state.activeProgramSet.id ? '/' + $scope.state.activeProgramSet.id : ''),
          method: ($scope.state.activeProgramSet.id ? 'PUT' : 'POST'),
          data: {
            name: $scope.state.activeProgramSet.name,
            programs: $scope.state.programs
          }})
          .success(function (response) {
            if(response.id) {
              $scope.state.activeProgramSet.id = response.id;
            }
          });
      }
    };

    // Opens a modal for editing an existing program.
    $scope.openEditProgramModal = function ($event, program) {
      if ($event) {
        $event.preventDefault();
      }

      return programSetModalService.openProgramModal(program, predefined, availableParameters.data.parameters).result.then(
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

      return programSetModalService.openProgramModal(program, predefined, availableParameters.data.parameters).result.then(
        function (newProgram) {
          $scope.state.programs.push(newProgram);
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

      return programSetModalService.openProgramModal(program, predefined, availableParameters).result.then(
        function (newProgram) {
          $scope.state.programs.push(newProgram);
        }
      );
    };

  });
});
