define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    $timeout, modalService, predefined, availableParameters, UserManager, activeProject) {

    const openProject = activeProject.getProjectFor(UserManager.data);
    if(!openProject) {
      modalService.informError([{message: 'There is no project open currently.'}]);
    }

    const defaultProgramSet = {name:'Default'};

    $scope.state = {
      programSetList: [defaultProgramSet],
      activeProgramSet: defaultProgramSet
    };

    $scope.addProgramSet = function () {
      var add = function (name) {
        const addedProgramSet = {name:name};
        $scope.state.programSetList[$scope.state.programSetList.length] = addedProgramSet;
        $scope.state.activeProgramSet = addedProgramSet;
      };

      programSetModalService.addProgramSet( add , $scope.state.programSetList);
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
        programSetModalService.editProgramSet($scope.state.activeProgramSet.name, edit, $scope.state.programSetList, 'Edit program set', true);
      }
    };

    $scope.deleteProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          $scope.state.programSetList = _.filter($scope.state.programSetList, function (programSet) {
            return programSet.name !== $scope.state.activeProgramSet.name;
          });
          $scope.state.activeProgramSet = $scope.state.programSetList ? $scope.state.programSetList[0] : void 0;
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
        programSetModalService.copyProgramSet($scope.state.activeProgramSet.name, copy.bind(this), $scope.state.programSetList);
      }
    };

    $scope.categories = predefined.categories;
    $scope.programs = predefined.programs;

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
          url: '/project/progsets/' + openProject.id,
          method: 'POST',
          data: {
            name: $scope.state.activeProgramSet.name,
            programs: $scope.programs
          }})
         .success(function (response) {
         });
      }
    }

  });
});
