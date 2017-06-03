define(['angular', 'ui.router'], function(angular) {

  'use strict';

  var module = angular.module('app.admin-projects', ['ui.router']);

  module.config(function($stateProvider) {
    $stateProvider
      .state('adminprojects', {
        url: '/admin-projects',
        templateUrl: 'js/modules/admin/projects.html?cacheBust=xxx',
        controller: 'AdminManageProjectsController',
      });
  });

  module.controller('AdminManageProjectsController', function($scope, rpcService, userManager, modalService, projectService, $state, toastr) {

    projectService
      .getAllProjectList()
      .then(function(response) {
        $scope.projects = response.data.projects;

        return rpcService.rpcRun('get_user_summaries');
      })
      .then(function(response) {
        $scope.users = _.map(
          response.data.users,
          function(user) {

            var userProjects = _.filter(
              $scope.projects, function(p) {
                return p.userId == user.id;
              });

            _.each(userProjects, function(project) {
              project.creationTime = Date.parse(project.creationTime);
              project.updatedTime = Date.parse(project.updatedTime);
              project.dataUploadTime = Date.parse(project.dataUploadTime);
            });

            return {
              data: user,
              projects: userProjects
            };
          }
        );
      });

    $scope.projectService = projectService;

    console.log('$scope.users', $scope.users);

    function getProjectNames() {
      return _.pluck(projectService.projects, 'name');
    }

    $scope.open = function(name, id) {
      projectService.setActiveProjectId(id);
    };

    $scope.editProjectName = function(project) {
      modalService.rename(
        function(name) {
          project.name = name;
          projectService
            .renameProject(project.id, project)
            .then(function() {
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

    $scope.copy = function(name, projectId) {
      projectService
        .copyProject(
          projectId,
          rpcService.getUniqueName(name, getProjectNames()))
        .then(function() {
          toastr.success('Copied project');
          $state.reload();
        });
    };

    $scope.downloadSpreadsheet = function(name, id) {
      rpcService.rpcDownload(
        'download_data_spreadsheet', [id], {'is_blank': false})
        .then(function(response) {
          toastr.success('Spreadsheet downloaded');
        });
    };

    $scope.downloadProject = function(name, id) {
      rpcService
        .rpcDownload(
          'download_project', [id])
        .then(function() {
          toastr.success('Project downloaded');
        });
    };

    $scope.deleteProject = function(id) {
      rpcService
        .rpcRun(
          'delete_projects', [[id]])
        .then(function() {
          toastr.success('Project deleted');
        });
    };

  });

  return module;

});
