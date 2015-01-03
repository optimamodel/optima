/**
 * ProjectOpenController can set a project as active
 * and allows to remove and create new projects.
 */

define([
  'angular',
  'ui.router',
  '../common/active-project-service',
  '../resources/project'
], function (angular) {
  'use strict';

  return angular.module('app.project', [
    'app.active-project',
    'app.resources.project',
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
            parametersResponse: function($http) {
              return $http.get('/api/project/params');
            },
            defaultsResponse: function($http) {
              return $http.get('/api/project/predefined')
            },
            info: function() {
              return undefined;
            }
          }
        })
        .state('project.edit', {
          url: '/edit',
          templateUrl: 'js/modules/project/create-or-edit.html',
          controller: 'ProjectCreateOrEditController',
          resolve: {
            parametersResponse: function($http) {
              return $http.get('/api/project/params');
            },
            defaultsResponse: function($http) {
              return $http.get('/api/project/predefined')
            },
            info: function (Project, activeProject) {
              if (activeProject.isSet()) {
                return Project.info().$promise;
              } else {
                return undefined;
              }
            }
          }
        })
        .state('project.open', {
          url: '/open',
          templateUrl: 'js/modules/project/open.html',
          controller: 'ProjectOpenController',
          resolve: {
            projects: function (Project) {
              return Project.list().$promise;
            }
          }
        });
    });
});
