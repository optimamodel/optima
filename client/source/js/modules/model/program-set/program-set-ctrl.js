define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    $timeout, modalService, predefined, availableParameters, UserManager, activeProject) {

    $scope.state = {};

    const resetPrograms = function() {
      $scope.categories = predefined.categories;
      $scope.programs = predefined.programs;
    };
    resetPrograms();

    $scope.setActivePrograms = function(program) {
      if (program) {
        $scope.state.activeProgramSet = program;
        if (program.programs) {
          $scope.programs = angular.copy(program.programs);
        } else {
          resetPrograms();
        }
      }
    };
    resetPrograms();

    const openProjectStr = activeProject.getProjectFor(UserManager.data);
    const openProject = openProjectStr ? JSON.parse(openProjectStr) : void 0;

    if(!openProject) {
      modalService.informError([{message: 'There is no project open currently.'}]);
    }

    $http({
      url: '/api/project/progsets/' + openProject.id,
      method: 'GET'})
      .success(function (response) {
        $scope.state.programSetList = response.progsets || [];
        if(response.progsets && response.progsets.length > 0) {
          $scope.setActivePrograms(response.progsets[0]);
        }
      });

    $scope.addProgramSet = function () {
      var add = function (name) {
        const addedProgramSet = {name:name};
        $scope.state.programSetList[$scope.state.programSetList.length] = addedProgramSet;
        $scope.state.activeProgramSet = addedProgramSet;
        resetPrograms();
      };
      programSetModalService.openProgramSetModal(null, add, $scope.state.programSetList, 'Add program set', true);
    };

    $scope.editProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        // This removing existing enter from array of programSetList and re-adding it with updated name was needed,
        // coz it turns out that angular does not refreshes the select unless there is change in its size.
        // https://github.com/angular/angular.js/issues/10939
        var edit = function (name) {
          $scope.state.programSetList = _.filter($scope.state.programSetList, function (programSet) {
            return programSet.name !== $scope.state.activeProgramSet.name;
          });
          $timeout(function () {
            $scope.state.activeProgramSet.name = name;
            $scope.state.programSetList[$scope.state.programSetList.length] = $scope.state.activeProgramSet;
          });
        };
        programSetModalService.openProgramSetModal($scope.state.activeProgramSet.name, edit, $scope.state.programSetList, 'Edit program set');
      }
    };

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
          $scope.state.programSetList ? $scope.setActivePrograms($scope.state.programSetList[0]) : void 0;
          $scope.state.programSetList = angular.copy($scope.state.programSetList);
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

    $scope.copyProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var copy = function (name) {
          const copiedProgramSet = {name: name};
          $scope.state.programSetList[$scope.state.programSetList.length] = copiedProgramSet;
          $scope.state.activeProgramSet = copiedProgramSet;
        };
        programSetModalService.openProgramSetModal($scope.state.activeProgramSet.name, copy, $scope.state.programSetList, 'Copy program set');
      }
    };

    /*
     * Opens a modal for editing an existing program.
     */
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

      return programSetModalService.openProgramModal(program, predefined, availableParameters).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

    $scope.saveProgramSet = function() {
      if (!openProject) {
        modalService.informError([{message: 'Open project before proceeding.'}]);
      } else {
        $http({
          url: 'api/project/progsets/' + openProject.id + ($scope.state.activeProgramSet.id ? '/' + $scope.state.activeProgramSet.id : ''),
          method: ($scope.state.activeProgramSet.id ? 'PUT' : 'POST'),
          data: {
            name: $scope.state.activeProgramSet.name,
            programs: $scope.programs
          }})
         .success(function (response) {
           if(response.id) {
             $scope.state.activeProgramSet.id = response.id;
             console.log('$scope.programs', $scope.state.programSetList);
           }
         });
      }
    }

  });
});
