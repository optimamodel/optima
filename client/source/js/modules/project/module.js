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
          templateUrl: 'js/modules/project/create.html',
          controller: 'ProjectCreateController',
          resolve: {
            parametersResponse: function($http) {
              return $http.get('/api/analysis/scenarios/params');
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
