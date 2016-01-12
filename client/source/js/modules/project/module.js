/**
 * ProjectOpenController can set a project as active
 * and allows to remove and create new projects.
 */

define([
  'angular',
  'ui.router',
  '../common/active-project-service',
  '../common/update-checkbox-on-click-directive',
  '../common/file-upload-service'
], function (angular) {
  'use strict';

  return angular.module('app.project', [
    'app.active-project',
    'app.common.update-checkbox-on-click',
    'app.common.file-upload',
    'ui.router'
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('project', {
          url: '/project',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('project.create', {
          url: '/create',
          templateUrl: 'js/modules/project/create-or-edit.html',
          controller: 'ProjectCreateOrEditController',
          resolve: {
            populations: function(projectApiService) {
              return projectApiService.getPopulations();
            },
            info: function() {
              return undefined;
            },
            projects: function (projectApiService) {
              return projectApiService.getProjectList();
            }
          }
        })
        .state('project.edit', {
          url: '/edit',
          templateUrl: 'js/modules/project/create-or-edit.html',
          controller: 'ProjectCreateOrEditController',
          resolve: {
            parametersResponse: function(projectApiService) {
              return projectApiService.getParameters();
            },
            populations: function(projectApiService) {
              return projectApiService.getPopulations();
            },
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            },
            projects: function (projectApiService) {
              return projectApiService.getProjectList();
            }
          }
        })
        .state('project.open', {
          url: '/open',
          templateUrl: 'js/modules/project/open.html',
          controller: 'ProjectOpenController',
          resolve: {
            projects: function (projectApiService) {
              return projectApiService.getProjectList();
            }
          }
        })
        .state('project.upload', {
          url: '/upload',
          templateUrl: 'js/modules/project/upload.html',
          controller: 'ProjectUploadController',
          resolve: {
            projects: function (projectApiService) {
              return projectApiService.getProjectList();
            }
          }
        });
    });
});
