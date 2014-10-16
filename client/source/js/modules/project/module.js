define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.project', ['ui.router'])
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
        .state('project.modify', {
          url: '/modify',
          templateUrl: 'js/modules/project/modify.html',
          controller: 'ProjectModifyController'
        });
    });

});
