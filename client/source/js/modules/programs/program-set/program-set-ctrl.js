define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    modalService, toastr, currentProject, projectApiService, $upload) {

    var project = currentProject.data;
    var defaultPrograms;
    var parameters;

    function initialize() {
      // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
      if (!project.hasData) {
        modalService.inform(
          function() { },
          'Okay',
          'Please upload spreadsheet to proceed.',
          'Cannot proceed'
        );
        $scope.missingData = true;
        return;
      }

      // Get the list of saved programs from DB and set the first one as active
      $http
        .get('/api/project/' + project.id + '/progsets')
        .success(function(response) {
          if (response.progsets) {
            $scope.programSetList = response.progsets;
            console.log("loaded_programs = ", $scope.programSetList);
            if (response.progsets && response.progsets.length > 0) {
              $scope.activeProgramSet = response.progsets[0];
            }
          }
        });

      // Fetching default categories and programs for the open project
      projectApiService
        .getDefault(project.id)
        .success(function(response) {
          defaultPrograms = response;
          console.log("default_programs = ", defaultPrograms);
        });

      // Get the list of default parameters for the project
      $http
        .get('/api/project/' + project.id + '/parameters')
        .success(function(response) {
          parameters = response.parameters;
        });
    }

    $scope.getCategories = function() {
      $scope.activeProgramSet.programs.sort();
      var categories = _.uniq(_.pluck($scope.activeProgramSet.programs, "category"));
      var i = categories.indexOf('Other');
      categories.splice(i, 1);
      categories.sort();
      categories.push('Other');
      return categories;
    };

    // Open pop-up to add new programSet
    $scope.addProgramSet = function () {
      var add = function (name) {
        var newProgramSet = {name:name, programs: angular.copy(defaultPrograms.programs)};
        $scope.programSetList[$scope.programSetList ? $scope.programSetList.length : 0] = newProgramSet;
        $scope.activeProgramSet = newProgramSet;
        $scope.saveActiveProgramSet('Progset added');
      };
      programSetModalService.openProgramSetModal(add, 'Add program set', $scope.programSetList, null, 'Add');
    };

    // Open pop-up to re-name programSet
    $scope.renameProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var rename = function (name) {
          $scope.activeProgramSet.name = name;
          $scope.saveActiveProgramSet('Progset renamed');
        };
        programSetModalService.openProgramSetModal(rename, 'Rename program set', $scope.programSetList, $scope.activeProgramSet.name, 'Update', true);
      }
    };

    // Download  programs data
    $scope.downloadProgramSet = function() {
      if(!$scope.activeProgramSet.id) {
        modalService.inform(
          _.noopt,
          'Okay',
          'Please save the program set to proceed.',
          'Cannot proceed'
        );
      } else {
        $http
          .get(
            '/api/project/' + project.id +  '/progsets' + '/' + $scope.activeProgramSet.id +'/data',
            {headers: {'Content-type': 'application/octet-stream'}, responseType:'blob'})
          .success(function (response) {
            var blob = new Blob([response], { type: 'application/octet-stream' });
            saveAs(blob, ($scope.activeProgramSet.name + '.prj'));
          });
      }
    };

    $scope.uploadProgramSet = function() {
      if(!$scope.activeProgramSet.id) {
        modalService.inform(
          function (){ },
          'Okay',
          'Please save the program set to proceed.',
          'Cannot proceed'
        );
      } else {
        angular
          .element('<input type=\'file\'>')
          .change(function (event) {
            $upload.upload({
              url: '/api/project/' + project.id + '/progsets' + '/' + $scope.activeProgramSet.id + '/data',
              file: event.target.files[0]
            }).success(function () {
              window.location.reload();
            });
          }).click();
      }
    };

    $scope.deleteProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          if ($scope.activeProgramSet.id) {
            $http
              .delete('/api/project/' + project.id +  '/progset' + '/' + $scope.activeProgramSet.id)
              .success(deleteProgramSetFromPage);
          } else {
            deleteProgramSetFromPage();
          }
        };
        modalService.confirm(
          remove,
          function () { },
          'Yes, remove this program set',
          'No',
          'Are you sure you want to permanently remove program set "' + $scope.activeProgramSet.name + '"?',
          'Delete program set'
        );
      }
    };

    function deleteProgramSetFromPage() {
      $scope.programSetList = _.filter($scope.programSetList, function(programSet) {
        return programSet.name !== $scope.activeProgramSet.name;
      });

      if ($scope.programSetList && $scope.programSetList.length > 0) {
        $scope.activeProgramSet = $scope.programSetList[0];
        console.log('set active program set', $scope.activeProgramSet.name);
      } else {
        $scope.activeProgramSet = undefined;
        console.log('undefined active program set');
      }

      toastr.success("Program set deleted");
    }

    $scope.copyProgramSet = function () {
      if (!$scope.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var copy = function (name) {
          var copiedProgramSet = {name: name, programs: $scope.activeProgramSet.programs};
          $scope.programSetList[$scope.programSetList.length] = copiedProgramSet;
          $scope.activeProgramSet = copiedProgramSet;
          $scope.saveActiveProgramSet("Program set copied");
        };
        programSetModalService.openProgramSetModal(
            copy, 'Copy program set', $scope.programSetList, $scope.activeProgramSet.name + ' copy', 'Copy');
      }
    }

    $scope.saveActiveProgramSet = function(msg) {
      if (!msg) {
        msg = 'Changes saved';
      }
      var programSet = $scope.activeProgramSet;
      if (!programSet || !programSet.name) {
        modalService.inform(
          function (){ },
          'Okay',
          'Please create a new program set before trying to save it.',
          'Cannot proceed'
        );
      } else {
        var method, url;
        if (programSet.id) {
          method = 'PUT';
          url = '/api/project/' + project.id + '/progset/' + programSet.id;
        } else {
          method = 'POST';
          url = '/api/project/' + project.id + '/progsets';
        }
        $http(
          {url: url, method: method, data: programSet})
        .success(function (response) {
          if(response.id) {
            $scope.activeProgramSet.id = response.id;
          }
          toastr.success(msg);
        });
      }
    };

    // Opens a modal for editing an existing program.
    $scope.openEditProgramModal = function ($event, program) {
      var editProgram = angular.copy(program);
      editProgram.short = editProgram.short || editProgram.short;
      return programSetModalService
        .openProgramModal(
          editProgram, project, $scope.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
          $scope.activeProgramSet.programs[$scope.activeProgramSet.programs.indexOf(program)] = newProgram;
          $scope.saveActiveProgramSet("Changes saved");
        });
    };

    $scope.changeProgramActive = function(program) {
        $scope.saveActiveProgramSet("Program active state saved");
    };

    // Creates a new program and opens a modal for editing.
    $scope.openAddProgramModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var program = {};

      return programSetModalService
        .openProgramModal(
            program, project, $scope.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
          $scope.activeProgramSet.programs.push(newProgram);
          $scope.saveActiveProgramSet("Program added");
        });
    };

    // Makes a copy of an existing program and opens a modal for editing.
    $scope.copyProgram = function ($event, existingProgram) {
      if ($event) {
        $event.preventDefault();
      }
      var program = angular.copy(existingProgram);
      program.name = program.name + ' copy';
      program.short = (program.short || program.short ) + ' copy';
      program.short = undefined;

      return programSetModalService
        .openProgramModal(
          program, project, $scope.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
          $scope.activeProgramSet.programs.push(newProgram);
          $scope.saveActiveProgramSet("Copied program");
        });
    };

    initialize();

  });
});
