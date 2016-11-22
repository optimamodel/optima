/**
 * ProjectOpenController can set a project as active
 * and allows to remove and create new projects.
 */

define(
  [
    'angular',
    'ui.router',
    '../common/active-project-service',
  ],
  function (angular) {
    'use strict';

    return angular.module('app.project', [
      'app.active-project',
      'ui.router'
    ])
      .config(function ($stateProvider) {
        $stateProvider
          .state('home', {
            url: '/',
            templateUrl: 'js/modules/project/manage-projects.html',
            controller: 'ProjectOpenController',
            resolve: {
              projects: function (projectApi) {
                return projectApi.getProjectList();
              }
            }
          })
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
              populations: function(projectApi) {
                return projectApi.getPopulations();
              },
              info: function() {
                return undefined;
              },
              projects: function (projectApi) {
                return projectApi.getProjectList();
              }
            }
          })
          .state('project.edit', {
            url: '/edit',
            templateUrl: 'js/modules/project/create-or-edit.html',
            controller: 'ProjectCreateOrEditController',
            resolve: {
              populations: function(projectApi) {
                return projectApi.getPopulations();
              },
              info: function (projectApi) {
                return projectApi.getActiveProject();
              },
              projects: function (projectApi) {
                return projectApi.getProjectList();
              }
            }
          })
          .state('project.upload', {
            url: '/upload',
            templateUrl: 'js/modules/project/upload.html',
            controller: 'ProjectUploadController',
            resolve: {
              projects: function (projectApi) {
                return projectApi.getProjectList();
              }
            }
          })
          .state('project.economicdata', {
            url: '/economic-data',
            templateUrl: 'js/modules/project/economic-data.html',
            controller: 'ProjectEconomicDataController',
            resolve: {
              info: function (projectApi) {
                return projectApi.getActiveProject();
              },
              projects: function (projectApi) {
                return projectApi.getProjectList();
              }
            }
          });
      });
  });
