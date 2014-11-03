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
  angular.injector(['ng', 'app.resources.project', 'app.active-project'])
    .invoke(['Project', 'activeProject', function (Project, activeProject) {
      Project
        .getCurrent(function (project) {
          activeProject.name = project.project;
        })
        .$promise
        .finally(function () {
          angular.bootstrap(document, ['app']);
        });
    }]);
});
