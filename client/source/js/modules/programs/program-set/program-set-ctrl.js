define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProgramSetController', function ($scope, $http, programSetModalService,
    modalService, toastr, currentProject, projectApiService, $upload, $state) {

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
            console.log("loaded program sets", $scope.programSetList);
            if (response.progsets && response.progsets.length > 0) {
              $scope.state.activeProgramSet = response.progsets[0];
            }
          }
        });

      // Load a default set of inactive programs for new
      projectApiService
        .getDefault(project.id)
        .success(function(response) {
          defaultPrograms = response;
          console.log("default_programs = ", defaultPrograms);
        });

      // Load parameters that can be used to set custom programs
      $http
        .get('/api/project/' + project.id + '/parameters')
        .success(function(response) {
          parameters = response.parameters;
        });
    }

    function deepCopyJson(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
    }

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
      programSetModalService.openProgramSetModal(add, 'Add program set', $scope.programSetList, null, 'Add');
    };

    // Open pop-up to re-name programSet
    $scope.renameProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var rename = function (name) {
          $scope.state.activeProgramSet.name = name;
          $scope.saveActiveProgramSet('Progset renamed');
        };
        programSetModalService.openProgramSetModal(rename, 'Rename program set', $scope.programSetList, $scope.state.activeProgramSet.name, 'Update', true);
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

    $scope.deleteProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var remove = function () {
          if ($scope.state.activeProgramSet.id) {
            $http
              .delete('/api/project/' + project.id +  '/progset' + '/' + $scope.state.activeProgramSet.id)
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
          'Are you sure you want to permanently remove program set "' + $scope.state.activeProgramSet.name + '"?',
          'Delete program set'
        );
      }
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

    function getUniqueName(name, otherNames) {
      var i = 0;
      var uniqueName = name;
      while (_.indexOf(otherNames, uniqueName) >= 0) {
        i += 1;
        uniqueName = name + ' (' + i + ')';
      }
      return uniqueName;
    }

    $scope.copyProgramSet = function () {
      if (!$scope.state.activeProgramSet) {
        modalService.informError([{message: 'No program set selected.'}]);
      } else {
        var copy = function (name) {
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
        var usedNames = _.pluck($scope.programSetList, 'name');
        programSetModalService.openProgramSetModal(
            copy,
            'Copy program set',
            $scope.programSetList,
            getUniqueName($scope.state.activeProgramSet.name, usedNames),
            'Copy');
      }
    };

    $scope.saveActiveProgramSet = function(msg) {
      if (!msg) {
        msg = 'Changes saved';
      }
      var programSet = $scope.state.activeProgramSet;
      console.log('saving', programSet);
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

    $scope.openEditProgramModal = function ($event, program) {
      var editProgram = angular.copy(program);
      editProgram.short = editProgram.short || editProgram.short;
      return programSetModalService
        .openProgramModal(
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

      return programSetModalService
        .openProgramModal(
            program, project, $scope.state.activeProgramSet.programs, parameters, $scope.getCategories())
        .result
        .then(function (newProgram) {
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

      return programSetModalService
        .openProgramModal(
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
