define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.project', ['ui.router'])
    .config(['$stateProvider', function ($stateProvider) {
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
        .state('project.upload-data', {
          url: '/upload-data',
          templateUrl: 'js/modules/project/upload-data.html',
          controller: 'ProjectUploadDataController'
        })
        .state('project.load', {
          url: '/load',
          templateUrl: 'js/modules/project/load.html',
          controller: 'ProjectLoadController'
        })
        .state('project.modify', {
          url: '/modify',
          templateUrl: 'js/modules/project/modify.html',
          controller: 'ProjectModifyController'
        });
    }]);

});
