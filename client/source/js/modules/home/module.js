define([
  'angular',
  'ui.router',
  '../common/active-project-service',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.home', [
    'app.constants',
    'app.active-project',
    'ui.router'
  ]).config(function ($stateProvider) {
    $stateProvider
      .state('home', {
        url: '/',
        templateUrl: '/js/modules/home/home.html',
        controller: 'HomeController',
        resolve: {
          project: function (Project, activeProject) {
            if (activeProject.isSet()) {
              return Project.info().$promise;
            } else {
              return undefined;
            }
          }
        }
      });
  });

});
