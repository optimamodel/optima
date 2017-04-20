define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function (
      $scope, $modal, modalService, toastr, projectService, $upload, $state, util) {

    var project;
    var defaultPrograms;
    var parameters;

    function initialize() {
      $scope.state = {};
      $scope.projectService = projectService;
      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined(project) && (project.id !== projectService.project.id)) {
          console.log('ProgramSetController project-change', projectService.project.name);
          reloadActiveProject();
        }
      });
      reloadActiveProject();
    }

    function reloadActiveProject() {
      projectService
        .getActiveProject()
        .then(function(response) {
          project = response.data;
          console.log('reloadActiveProject', project);
          $scope.isMissingData = !project.hasParset;
          if ($scope.isMissingData) {
            return;
          }

          // Load program sets; set first as active
          return util.rpcRun('load_progset_summaries', [project.id])
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

          // Load a default set of inactive programs for new
          return projectService.getDefaultPrograms(project.id)
        })
        .then(function(response) {
          defaultPrograms = response.data.programs;
          console.log("ProgramSetController.init defaultPrograms", defaultPrograms);

          // Load parameters that can be used to set custom programs
          return util.rpcRun('load_project_parameters', [project.id]);
        })
        .then(function(response) {
          parameters = response.data.parameters;
          console.log("ProgramSetController.init parameters", parameters);
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
        var newProgramSet = {name:name, programs: angular.copy(defaultPrograms.programs)};
        $scope.programSetList[$scope.programSetList ? $scope.programSetList.length : 0] = newProgramSet;
        $scope.state.activeProgramSet = newProgramSet;
        $scope.saveActiveProgramSet('Progset added');
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
          util
            .rpcRun(
              'rename_progset', [project.id, $scope.state.activeProgramSet.id, name])
            .then(function(response) {
              $scope.state.activeProgramSet.name = name;
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
      util
        .rpcDownload(
          'download_project_object',
          [projectService.project.id, 'progset', $scope.state.activeProgramSet.id])
        .then(function(response) {
          toastr.success('Progset downloaded');
        });
    };

    $scope.uploadProgramSet = function() {
      util
        .rpcUpload(
          'upload_project_object', [projectService.project.id, 'progset'])
        .then(function(response) {
          toastr.success('Progset uploaded');
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
          util
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
          util
            .rpcRun(
              'copy_progset', [project.id, $scope.state.activeProgramSet.id, name])
            .then(function(response) {
              $scope.programSetList = response.data.progsets;
              console.log("loaded program sets", $scope.programSetList);
              $scope.state.activeProgramSet = _.findWhere($scope.programSetList, {name:name});
            });
        };
        var names = _.pluck($scope.programSetList, 'name');
        var name = $scope.state.activeProgramSet.name;
        copy(modalService.getUniqueName(name, names));
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
        util
          .rpcRun(
            'save_progset', [project.id, programSet.id, programSet])
          .then(function(response) {
            $scope.state.activeProgramSet.id = response.data.id;
            toastr.success(successMessage);
          });
      } else {
        util
          .rpcRun(
            'create_progset', [project.id, programSet])
          .then(function(response) {
            console.log('saveActiveProgramSet create', response);
            _.assign($scope.state.activeProgramSet, response.data);
            toastr.success(successMessage);
          });
      }
    };


    /* Program functions */

    function openProgramModal(program, openProject, programList, parameters, categories) {
      return $modal.open({
        templateUrl: 'js/modules/programs/program-set/program-modal.html',
        controller: 'ProgramModalController',
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
});
