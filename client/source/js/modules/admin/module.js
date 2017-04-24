define(['angular', 'ui.router', ], function (angular) {

    'use strict';

    var module = angular.module('app.admin', ['ui.router']);

    module.config(function($stateProvider) {
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
            })
            .state('admin.manage-projects', {
                url: '/manage-projects',
                templateUrl: 'js/modules/admin/manage-projects.html' ,
                controller: 'AdminManageProjectsController',
            });
    });

    return module;
});
