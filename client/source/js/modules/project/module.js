define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.project', ['ui.router'])

    .config(function ($stateProvider) {

      $stateProvider
        .state('home', {
          url: '/',
          templateUrl: 'js/modules/project/manage-projects.html',
          controller: 'ProjectOpenController'
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
        })
    });
});
