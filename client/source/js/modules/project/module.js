define([
  'angular',
  'ui.router',
  '../resources/project'
], function (angular) {
  'use strict';

  return angular.module('app.project', [
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
          controller: 'ProjectCreateController'
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
