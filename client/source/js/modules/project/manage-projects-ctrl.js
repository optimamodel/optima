define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller(
    'ProjectOpenController',
    function($scope, $http, util, modalService, userManager, projectApi, $state, $upload, $modal, toastr) {

      function initialize() {
        $scope.sortType = 'name'; // set the default sort type
        $scope.sortReverse = false;  // set the default sort order
        $scope.projectApi = projectApi;
      }

      function getProjectNames() {
        return _.pluck(projectApi.projects, 'name');
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
        _.forEach(projectApi.projects, function(project) {
          project.selected = $scope.allSelected;
        });
      };

      $scope.deleteSelected = function() {
        const selectedProjectIds = _.filter(projectApi.projects, function(project) {
          return project.selected;
        }).map(function(project) {
          return project.id;
        });
        projectApi
          .deleteSelectedProjects(selectedProjectIds)
      };

      $scope.downloadSelected = function() {
        const selectedProjectsIds =
          _.filter(
            projectApi.projects,
            function(project) { return project.selected; })
          .map(
            function(project) { return project.id; });
        projectApi
          .downloadSelectedProjects(selectedProjectsIds)
          .success(function (response) {
            saveAs(new Blob([response], { type: "application/octet-stream", responseType: 'arraybuffer' }), 'portfolio.zip');
          });
      };

      $scope.open = function (name, id) {
        projectApi.setActiveProjectId(id);
      };

      $scope.copy = function(name, projectId) {
        projectApi
          .copyProject(
            projectId,
            util.getUniqueName(name, getProjectNames()))
          .then(function() {
            toastr.success('Copied project');
            $state.reload();
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
        projectApi
          .uploadProject()
          .then(function() {
            toastr.success('Project uploaded');
          });
      };

      $scope.uploadProjectFromSpreadsheet = function() {
        projectApi
          .uploadProjectFromSpreadsheet()
          .then(function() {
            toastr.success('Project uploaded from spreadsheet');
          });
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
        modalService.rename(
          function(name) {
            project.name = name;
            projectApi
              .renameProject(project.id, project)
              .then(function () {
                toastr.success('Renamed project');
                $state.reload();
              });
          },
          'Edit project name',
          "Enter project name",
          project.name,
          "Name already exists",
          _.without(getProjectNames(), project.name));
      };

      $scope.downloadProject = function (name, id) {
        util
          .rpcDownload(
            'download_project', [id])
          .then(function() {
            toastr.success('Project downloaded');
          });
      };

      $scope.downloadPrjWithResults = function (name, id) {
        util
          .rpcDownload(
            'download_project_with_result', [id])
          .then(function() {
            toastr.success('Project downloaded');
          });
      };

      $scope.remove = function ($event, name, id, index) {
        if ($event) { $event.preventDefault(); }
        var message = 'Are you sure you want to permanently remove project "' + name + '"?';
        modalService.confirm(
          function() {
            projectApi
              .deleteProject(id)
              .then(function(response) {
                toastr.success('Deleted project');
                $state.reload();
              });
          },
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

