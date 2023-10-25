define(['angular', 'ui.router', './program-modal'], function (angular) {

  'use strict';

  var module = angular.module(
    'app.programs', ['ui.router', 'app.program-modal']);


  module.config(function($stateProvider) {
    $stateProvider
      .state('programs', {
        url: '/programs',
        templateUrl: 'js/modules/programs/programs.html?cacheBust=xxx',
        controller: 'ProgramSetController'
      });
  });


  module.controller('ProgramSetController', function (
      $scope, $modal, modalService, toastr, projectService, $upload, $state, rpcService) {

    var project;
    var defaultPrograms;
    var parameters;

    function initialize() {
      $scope.state = {};
      $scope.projectService = projectService;
      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined(project) && (project.id !== projectService.project.id)) {
          console.log('ProgramSetController project-change', projectService.project.name);
          reloadActiveProject(false);   // we're not using an Undo stack here
        }
      });

      // Load the active project, telling the function we're not using an Undo stack.
      reloadActiveProject(false);
    }

    function reloadActiveProject(useUndoStack) {
      projectService
        .getActiveProject()
        .then(function(response) {
          project = response.data;
          console.log('reloadActiveProject', project);
          $scope.isMissingData = !project.calibrationOK;
          if ($scope.isMissingData) {
            return;
          }

          // Load program sets; set first as active
          return rpcService.rpcRun('load_progset_summaries', [project.id])
        })
        .then(function(response) {
          var data = response.data;
          if (data.progsets) {
            $scope.programSetList = data.progsets;
            console.log("ProgramSetController.init progsets", $scope.programSetList);
            // Set first as active
            if (data.progsets && data.progsets.length > 0) {
              $scope.state.activeProgramSet = data.progsets[0];
            }
          }

          // Initialize a new UndoStack on the server if we are not using an UndoStack in this 
          // call.
		  if (!useUndoStack) {
            rpcService
              .rpcRun(
                'init_new_undo_stack', [project.id]);
		  }

          // Load a default set of inactive programs for new
          return projectService.getDefaultPrograms(project.id)
        })
        .then(function(response) {
          defaultPrograms = response.data.programs;
          console.log("ProgramSetController.init defaultPrograms", defaultPrograms);

          // Load parameters that can be used to set custom programs
          return rpcService.rpcRun('load_project_parameters', [project.id]);
        })
        .then(function(response) {
          parameters = response.data.parameters;
          console.log("ProgramSetController.init parameters", parameters);
        });
    }

	$scope.undo = function() {
      rpcService
        .rpcRun(
          'fetch_undo_project',
          [projectService.project.id])
        .then(function(response) {
		  if (response.data.didundo) {
		    reloadActiveProject(true);
            toastr.success('Undo to previous save complete');
          }
        });		
	}
	
	$scope.redo = function() {
      rpcService
        .rpcRun(
          'fetch_redo_project',
          [projectService.project.id])
        .then(function(response) {
		  if (response.data.didredo) {
		    reloadActiveProject(true);
            toastr.success('Redo to next save complete');
          }		  
        });      		
	}

    /* Program set functions */

    $scope.getCategories = function() {
      $scope.state.activeProgramSet.programs.sort();
      var categories = _.uniq(_.pluck($scope.state.activeProgramSet.programs, "category"));
      var i = categories.indexOf('Other');
      categories.splice(i, 1);
      categories.sort();
      categories.push('Other');
      return categories;
    };

    // Open pop-up to add new programSet
    $scope.addProgramSet = function () {
      var add = function (name) {

        // Call create_default_progset RPC.
        rpcService
          .rpcRun(
            'create_default_progset', [project.id, name])
          .then(function(response) {
            $scope.programSetList = response.data.progsets;
            console.log("loaded program sets", $scope.programSetList);
            $scope.state.activeProgramSet = _.findWhere($scope.programSetList, {name:name});
            toastr.success('Program set added');

            // Push the saved project to the UndoStack.
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [project.id]);
              });
      };
      modalService.rename(
        add,
        'Add program set',
        'Enter name',
        '',
        'Name already exists',
        _.pluck($scope.programSetList, 'name'));
    };

    // Open pop-up to re-name programSet
    $scope.renameProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        function rename(name) {
          rpcService
            .rpcRun(
              'rename_progset', [project.id, $scope.state.activeProgramSet.id, name])
            .then(function(response) {
              $scope.state.activeProgramSet.name = name;

              // Push the saved project to the UndoStack.
              rpcService
                .rpcRun(
                  'push_project_to_undo_stack', 
                  [project.id]);
            });
        }
        var name = $scope.state.activeProgramSet.name;
        var otherNames = _.pluck($scope.programSetList, 'name');
        modalService.rename(
          rename,
          'Rename program set',
          'Enter name',
          name,
          'Name already exists',
          _.without(otherNames, name)
        );
      }
    };

    $scope.downloadProgramSet = function() {
      rpcService
        .rpcDownload(
          'download_project_object',
          [projectService.project.id, 'progset', $scope.state.activeProgramSet.id])
        .then(function(response) {
          toastr.success('Program set downloaded');
        });
    };

    $scope.uploadProgramSet = function() {
      rpcService
        .rpcUpload(
          'upload_project_object', [projectService.project.id, 'progset'], {}, '.prg')
        .then(function(response) {
		  if (response.data.name == 'BadFileFormatError') {
			toastr.error('The file you have chosen is not valid for uploading');  
		  } else if (response.data.name == 'AddObjectError') {
              modalService.inform(angular.noop, 'Okay', '', 'Error adding object', response.data.message);
          } else {
            toastr.success('Program set uploaded');
            var name = response.data.name;

            // Push the saved project to the UndoStack.
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [project.id]);

            rpcService
              .rpcRun('load_progset_summaries', [projectService.project.id])
              .then(function(response) {
                var data = response.data;
                if (data.progsets) {
                  $scope.programSetList = data.progsets;
                  console.log("uploadProgramSet", $scope.programSetList);
                  $scope.state.activeProgramSet = _.findWhere(data.progsets, {name: name});
                }
              });
		  }
        });
    };

    function deleteProgramSetFromPage() {
      $scope.programSetList = _.filter($scope.programSetList, function(programSet) {
        return programSet.name !== $scope.state.activeProgramSet.name;
      });

      if ($scope.programSetList && $scope.programSetList.length > 0) {
        $scope.state.activeProgramSet = $scope.programSetList[0];
        console.log('set active program set', $scope.state.activeProgramSet.name);
      } else {
        $scope.state.activeProgramSet = undefined;
        console.log('undefined active program set');
      }

      toastr.success("Program set deleted");

      // Push the saved project to the UndoStack.
      rpcService
        .rpcRun(
          'push_project_to_undo_stack', 
          [project.id]);

      $state.reload();
    }


    $scope.deleteProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
        return;
      }

      if ($scope.programSetList.length == 1) {
        modalService.informError([{message: 'Cannot delete last program set.'}]);
        return;
      }

      modalService.confirm(
        function () {
          rpcService
            .rpcRun(
              'delete_progset', [project.id, $scope.state.activeProgramSet.id])
            .then(
              deleteProgramSetFromPage);
        },
        function () {},
        'Yes, remove this program set',
        'No',
        'Are you sure you want to permanently remove program set "' + $scope.state.activeProgramSet.name + '"?',
        'Delete program set'
      );

    };

    $scope.copyProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        function copy(name) {
          rpcService
            .rpcRun(
              'copy_progset', [project.id, $scope.state.activeProgramSet.id, name])
            .then(function(response) {
              $scope.programSetList = response.data.progsets;
              console.log("loaded program sets", $scope.programSetList);
              $scope.state.activeProgramSet = _.findWhere($scope.programSetList, {name:name});

              // Push the saved project to the UndoStack.
              rpcService
                .rpcRun(
                  'push_project_to_undo_stack', 
                  [project.id]);
            });
        };
        var names = _.pluck($scope.programSetList, 'name');
        var name = $scope.state.activeProgramSet.name;
        copy(rpcService.getUniqueName(name, names));
      }
    };

    $scope.saveActiveProgramSet = function(successMessage) {
      var programSet = $scope.state.activeProgramSet;
      console.log('saveActiveProgramSet', programSet);
      if (!programSet || !programSet.name) {
        modalService.inform(
          function (){ },
          'Okay',
          'Please create a new program set before trying to save it.',
          'Cannot proceed'
        );
        return;
      }

      if (!successMessage) {
        successMessage = 'Changes saved';
      }

      if (programSet.id) {
        rpcService
          .rpcRun(
            'save_progset', [project.id, programSet.id, programSet])
          .then(function(response) {
            $scope.state.activeProgramSet.id = response.data.id;
            toastr.success(successMessage);
            projectService.getActiveProject();

            // Push the saved project to the UndoStack.
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [project.id]);
          });
      } else {
        rpcService
          .rpcRun(
            'create_progset', [project.id, programSet])
          .then(function(response) {
            console.log('saveActiveProgramSet create', response);
            _.assign($scope.state.activeProgramSet, response.data);
            toastr.success(successMessage);
            projectService.getActiveProject();

            // Push the saved project to the UndoStack.
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [project.id]);
          });
      }
    };


    /* Program functions */

    function openProgramModal(program, openProject, programList, parameters, categories) {
      return $modal.open({
        templateUrl: 'js/modules/programs/program-modal.html?cacheBust=xxx',
        controller: 'ProgramModalController',
        backdrop: 'static',
        keyboard: false,
        size: 'lg',
        resolve: {
          program: function () { return program; },
          programList: function () { return programList; },
          openProject: function(){ return openProject; },
          populations: function () { return openProject.populations; },
          parameters: function() { return parameters; },
          categories: function() { return categories; }
        }
      });
    }

    $scope.openEditProgramModal = function ($event, program) {
      var editProgram = angular.copy(program);
      editProgram.short = editProgram.short || editProgram.short;
      return openProgramModal(
            editProgram, project, $scope.state.activeProgramSet.programs, parameters, $scope.getCategories())
          .result
          .then(function (newProgram) {
            $scope.state.activeProgramSet.programs[$scope.state.activeProgramSet.programs.indexOf(program)] = newProgram;
            $scope.saveActiveProgramSet("Changes saved");
          });
    };

    // Creates a new program and opens a modal for editing.
    $scope.openAddProgramModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var program = {};

      return openProgramModal(
            program, project, $scope.state.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
          console.log('openAddProgramModal', newProgram);
          $scope.state.activeProgramSet.programs.push(newProgram);
          $scope.saveActiveProgramSet("Program added");
        });
    };

    $scope.copyProgram = function ($event, existingProgram) {
      if ($event) {
        $event.preventDefault();
      }
      var program = angular.copy(existingProgram);
      program.name = program.name + ' copy';
      program.short = (program.short || program.short ) + ' copy';
      program.short = undefined;

      return openProgramModal(
          program, project, $scope.state.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
          $scope.state.activeProgramSet.programs.push(newProgram);
          $scope.saveActiveProgramSet("Copied program");
        });
    };

    initialize();

  });

  return module;

  });
