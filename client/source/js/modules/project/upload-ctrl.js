define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectUploadController',
    function ($scope, projects, modalService) {

    // Initialize Params
    $scope.projectParams = { name: "", file: undefined };

    $scope.uploadProject = function() {
      if ($scope.UploadProjectForm.$invalid) {
        modalService.informError([{message: 'Please fill in all the required project fields.'}]);
        return false;
      } else {
        console.log('upload project');
      }
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
