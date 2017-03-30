define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller(
    'ProjectOpenController',
    function ($scope, $http, activeProject, projects, util, modalService,
        userManager, projectApi, $state, $upload,
        $modal, toastr) {

      function initialize() {
        $scope.sortType = 'name'; // set the default sort type
        $scope.sortReverse = false;  // set the default sort order
        $scope.activeProject = activeProject;
        $scope.activeProjectId = activeProject.getProjectIdForCurrentUser();
        loadProjects(projects.data.projects);
        setActiveProject();
      }

      function setActiveProject() {
        $scope.project = null;
        _.each($scope.projects, function(project) {
          if ($scope.activeProjectId === project.id) {
            $scope.project = project;
          }
        });
      }

      function loadProjects(projects) {
        $scope.projects = _.map(projects, function(project) {
          // project.creationTime = Date.parse(project.creationTime);
          // project.updatedTime = Date.parse(project.updatedTime);
          // project.dataUploadTime = Date.parse(project.dataUploadTime);
          return project;
        });
        console.log('loadProjects ', $scope.projects);
      }

      $scope.filterByName = function(project) {
        if ($scope.searchTerm) {
          return project.name.toLowerCase().indexOf($scope.searchTerm.toLowerCase()) !== -1;
        }
        return true;
      };

      $scope.updateSorting = function(sortType) {
        if ($scope.sortType === sortType) {
          $scope.sortReverse = !$scope.sortReverse;
        } else {
          $scope.sortType = sortType;
        }
      };

      $scope.selectAll = function() {
        _.forEach($scope.projects, function(project) {
          project.selected = $scope.allSelected;
        });
      };

      $scope.deleteSelected = function() {
        const selectedProjectIds = _.filter($scope.projects, function(project) {
          return project.selected;
        }).map(function(project) {
          return project.id;
        });
        projectApi.deleteSelectedProjects(selectedProjectIds)
          .success(function () {
            $scope.projects = _.filter($scope.projects, function(project) {
              return !project.selected;
            });
            _.each(selectedProjectIds, function(projectId) {
              activeProject.ifActiveResetFor(projectId, userManager.user);
            });
          });
      };

      $scope.downloadSelected = function() {
        const selectedProjectsIds = _.filter($scope.projects, function(project) {
          return project.selected;
        }).map(function(project) {
          return project.id;
        });
        projectApi.downloadSelectedProjects(selectedProjectsIds)
          .success(function (response) {
            saveAs(new Blob([response], { type: "application/octet-stream", responseType: 'arraybuffer' }), 'portfolio.zip');
          });
      };

      $scope.open = function (name, id) {
        $scope.activeProjectId = id;
        setActiveProject();
        activeProject.setActiveProjectFor(name, id, userManager.user);
      };

      function existingProjectName() {
        return _.pluck($scope.projects, 'name');
      }

      $scope.copy = function(name, id) {
        var newName = util.getUniqueName(name, existingProjectName());
        projectApi
          .copyProject(id, newName)
          .success(function(response) {
            projectApi
              .getProjectList()
              .success(function(response) {
                loadProjects(response.projects);
                var project = _.findWhere($scope.projects, {name: newName});
                activeProject.setActiveProjectFor(project.name, project.id, userManager.user);
                toastr.success('Copied project ');
                $state.reload();
              });
          });
      };

      $scope.downloadSpreadsheet = function (name, id) {
        $http
          .post(
            '/api/download',
            {
              'name': 'download_data_spreadsheet',
              'args': [id],
              'kwargs': {'is_blank': false}
            },
            {responseType: 'blob'})
          .success(function (response) {
            var blob = new Blob([response]);
            saveAs(blob, (name + '.xlsx'));
          });
      };

      $scope.uploadProject = function() {
        angular
          .element('<input type="file">')
          .change(function (event) {
            var file = event.target.files[0];
            var name = file.name;
            name = name.replace(/\.prj$/, "").replace(/\.xlsx$/, "");
            $upload
              .upload({
                url: '/api/project/data',
                fields: {name: util.getUniqueName(name, existingProjectName())},
                file: file
              })
              .success(function (data, status, headers, config) {
                var name = data['name'];
                var projectId = data['id'];
                toastr.success('Project uploaded');
                activeProject.setActiveProjectFor(
                  name, projectId, userManager.user);
                $state.reload();
              });
          })
          .click();
      };

      $scope.uploadProjectFromSpreadsheet = function() {
        angular
          .element('<input type="file">')
          .change(function (event) {
            var file = event.target.files[0];
            var name = file.name;
            name = name.replace(/\.prj$/, "").replace(/\.xlsx$/, "");
            $upload
              .upload({
                url: '/api/project/data',
                fields: {name: util.getUniqueName(name, existingProjectName()), xls: true},
                file: file
              })
              .success(function (data, status, headers, config) {
                var name = data['name'];
                var projectId = data['id'];
                activeProject.setActiveProjectFor(
                  name, projectId, userManager.user);
                toastr.success('Project created from spreadsheet');
                $state.reload();
              });
          })
          .click();
      };

      $scope.uploadSpreadsheet = function (name, id) {
        angular
          .element('<input type="file">')
          .change(function (event) {
            $upload
              .upload({
                url: '/api/project/' + id + '/spreadsheet',
                file: event.target.files[0]
              })
              .success(function (response) {
                toastr.success('Spreadsheet uploaded for project');
                $state.reload();
              });

          })
          .click();
      };

      $scope.editProjectName = function(project) {
        var otherNames = _.pluck($scope.projects, 'name');
        otherNames = _.without(otherNames, project.name)
        modalService.rename(
          function(name) {
            project.name = name;
            projectApi
              .updateProject(
                project.id,
                {
                  project: project,
                  isSpreadsheet: false,
                  isDeleteData: false,
                })
              .success(function () {
                project.name = name;
                toastr.success('Renamed project');
                activeProject.setActiveProjectFor(name, project.id, userManager.user);
                $state.reload();
              });
          },
          'Edit project name',
          "Enter project name",
          project.name,
          "Name already exists",
          otherNames);
      };

      $scope.downloadProject = function (name, id) {
        projectApi.downloadProjectFile(id)
          .success(function (response, status, headers, config) {
            var blob = new Blob([response], { type: 'application/octet-stream' });
            saveAs(blob, (name + '.prj'));
          });
      };

      $scope.downloadPrjWithResults = function (name, id) {
        $http.post(
          '/api/download',
          {
            'name': 'download_project_with_result',
            'args': [id]
          },
          {
            headers: {'Content-type': 'application/octet-stream'},
            responseType:'blob'
          })
          .then(function(response) {
            var blob = new Blob([response.data], {type: 'application/octet-stream'});
            saveAs(blob, (name + '.prj'));
          });
      };

      /**
       * Removes the project.
       */
      var removeProject = function (name, id, index) {
        projectApi.deleteProject(id).success(function (response) {
          $scope.projects = _($scope.projects).filter(function (item) {
            return item.id != id;
          });
          activeProject.ifActiveResetFor(id, userManager.user);
        });
      };

      /**
       * Opens a modal window to ask the user for confirmation to remove the project and
       * removes the project if the user confirms.
       * Closes it without further action otherwise.
       */
      $scope.remove = function ($event, name, id, index) {
        if ($event) { $event.preventDefault(); }
        var message = 'Are you sure you want to permanently remove project "' + name + '"?';
        modalService.confirm(
          function (){ removeProject(name, id, index); },
          function (){  },
          'Yes, remove this project',
          'No',
          message,
          'Remove project'
        );
      };

      initialize();
  });

});

