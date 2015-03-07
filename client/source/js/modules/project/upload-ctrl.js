define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectUploadController',
    function ($scope, projects) {

    // Initialize Params
    $scope.projectParams = { name: "" };

    $scope.uploadProject = function() {
      console.log('upload project');
    };

    $scope.projectExists = function() {
      var projectNames = _(projects.projects).map(function(project) {
        return project.name;
      });
      var exists = _(projectNames).contains($scope.projectParams.name);
      $scope.UploadProjectForm.ProjectName.$setValidity("projectExists", !exists);
      return exists;
    };
  });

});
