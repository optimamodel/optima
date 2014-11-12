/**
 * Bootstraps angular onto the window.document node.
 * NOTE: the ng-app attribute should not be on the index.html when using ng.bootstrap
 */
define([
  'angular',
  './app'
], function (angular) {
  'use strict';

  // You can place operations that need to initialize prior to app start here
  // using the `run` function on the top-level module
  angular.injector([
    'ng',
    'app.active-project',
    'app.resources.project',
    'app.resources.user'
  ])
    .invoke([
      '$q', 'activeProject', 'Project', 'User',
      function ($q, activeProject, Project, User) {

        User
          .getCurrent(function (user) {
            window.user = user;

            Project.getCurrent(function (project) {
              activeProject.name = project.project;
            });
          })
          .$promise
          .finally(function () {
            angular.bootstrap(document, ['app']);
          });

      }]);
});
