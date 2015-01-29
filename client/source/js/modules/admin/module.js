define([
    'angular',
    'ui.router',
    '../../config',
    '../resources/model',
], function (angular) {
    'use strict';

    return angular.module('app.admin', [
        'app.constants',
        'ui.router'
    ]).config(function ($stateProvider) {
        $stateProvider
            .state('admin', {
                url: '/admin',
                abstract: true,
                template: '<div ui-view></div>'
            })
            .state('admin.manage-users', {
                url: '/manage-users',
                templateUrl: 'js/modules/admin/manage-users.html' ,
                controller: 'AdminManageUsersController',
                resolve: {
                  info: function($http) {
                    return $http.get('/api/project/info');
                  },
                  users:function($http){
                    return $http.get('/api/user/list');
                  }
                }
            })
            .state('admin.manage-projects', {
                url: '/manage-projects',
                templateUrl: 'js/modules/admin/manage-projects.html' ,
                controller: 'AdminManageProjectsController',
                resolve: {
                  info: function($http) {
                    return $http.get('/api/project/info');
                  }
                }
            });
    });

});
