define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectUploadController',
    function ($scope, projects, modalService, $upload, $state) {

      $scope.onFileSelect = function(files) {
        $scope.projectParams.file = files[0];
      };

      // Initialize Params
      $scope.projectParams = { name: "", file: undefined };

      $scope.uploadProject = function() {
        if ($scope.UploadProjectForm.$invalid) {
          modalService.informError([{message: 'Please fill in all the required project fields.'}]);
          return false;
        } else {
          var fileName = $scope.projectParams.file.name;
          var fileExt = fileName.substr(fileName.lastIndexOf('.') + 1, fileName.length);
          if (fileExt !== 'json') {
            modalService.informError([{message: 'Please upload an Optima project file. This should have the file extension .json. ' +
            'If you are trying to upload a spreadsheet, use the "Upload Optima spreadsheet" option instead.'}]);
            return false;
          } else {
            $upload.upload({
              url: '/api/project/data',
              fields: {name: $scope.projectParams.name},
              file: $scope.projectParams.file
            }).success(function (data, status, headers, config) {
              $state.go('project.open');
            });
          }
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
    }
  );

});
