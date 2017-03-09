define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function (
      $scope, $http, $modal, modalService, toastr,
      currentProject, projectApi, $upload, $state) {

    var project = currentProject.data;
    var defaultPrograms;
    var parameters;

    function initialize() {

      $scope.isMissingData = !project.hasParset;
      if ($scope.isMissingData) {
        return;
      }

      // need to use state as there is an inherited scope
      // in this page, and writing to a property of an object
      // avoids the inherited scope problem. bleah.
      $scope.state = {};
      
      // Load program sets; set first as active
      $http
        .get(
            '/api/project/' + project.id + '/progsets')
        .success(function(response) {
          if (response.progsets) {
            $scope.programSetList = response.progsets;
            console.log("ProgramSetController.init progsets", $scope.programSetList);
            if (response.progsets && response.progsets.length > 0) {
              $scope.state.activeProgramSet = response.progsets[0];
            }
          }
        });

      // Load a default set of inactive programs for new
      projectApi
        .getDefault(project.id)
        .success(function(response) {
          defaultPrograms = response;
          console.log("ProgramSetController.init defaultPrograms", defaultPrograms);
        });

      // Load parameters that can be used to set custom programs
      $http
        .get('/api/project/' + project.id + '/parameters')
        .success(function(response) {
          parameters = response.parameters;
          console.log("ProgramSetController.init parameters", parameters);
        });
    }

    function deepCopyJson(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
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
        // Load parameters that can be used to set custom programs
        $http
          .put(
            '/api/project/' + project.id
              + '/progset/' + $scope.state.activeProgramSet.id
              + '/rename',
            { newName: name })
          .success(function(response) {
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
      var data = JSON.stringify(angular.copy($scope.state.activeProgramSet), null, 2);
      var blob = new Blob([data], { type: 'application/octet-stream' });
      saveAs(blob, ($scope.state.activeProgramSet.name + '.progset.json'));
    };

    $scope.uploadProgramSet = function() {
      angular
        .element('<input type=\'file\'>')
        .change(
          function(event) {
            $upload.upload({
              url: '/api/project/' + project.id
                    + '/progset/' + $scope.state.activeProgramSet.id
                    + '/data',
              file: event.target.files[0],
            }).success(function(programSet) {
              function isSameId(p) { return p.id === programSet.id; }
              var i = _.findIndex($scope.programSetList, isSameId);
              $scope.programSetList[i] = programSet;
              $scope.state.activeProgramSet = $scope.programSetList[i];
            });
          })
        .click();
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
          $http
            .delete(
              '/api/project/' + project.id +  '/progset' + '/' + $scope.state.activeProgramSet.id)
            .success(
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
          $http
            .post(
              '/api/project/' + project.id
              + '/progset/' + $scope.state.activeProgramSet.id,
              {name: name})
            .success(function(response) {
              $scope.programSetList = response.progsets;
              console.log("loaded program sets", $scope.programSetList);
              $scope.state.activeProgramSet = _.findWhere($scope.programSetList, {name:name});
            });
        };
        var names = _.pluck($scope.programSetList, 'name');
        var name = $scope.state.activeProgramSet.name;
        copy(modalService.getUniqueName(name, names));
      }
    };

    $scope.saveActiveProgramSet = function(msg) {
      if (!msg) {
        msg = 'Changes saved';
      }
      var programSet = $scope.state.activeProgramSet;
      console.log('saveActiveProgramSet', programSet);
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
            $scope.state.activeProgramSet.id = response.id;
          }
          toastr.success(msg);
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
