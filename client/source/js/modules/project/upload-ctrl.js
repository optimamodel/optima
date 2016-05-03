define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectUploadController',
    function ($scope, projects, modalService, $upload, $state, UserManager, activeProject) {

      // Initialize Params
      $scope.projectParams = { name: "", file: undefined };

      $scope.onFileSelect = function(files) {
        if (!files[0]) {
          return;
        }

        $scope.projectParams.file = files[0];

        // if no projectname given, automatically fill in name from file
        if (!$scope.projectParams.name) {
          var fileName = files[0].name;

          // if project name taken, try variants
          var i = 0;
          $scope.projectParams.name = fileName;
          while ($scope.projectExists()) {
            i += 1;
            $scope.projectParams.name = fileName + " (" + i + ")";
          }
        }
      };

      $scope.uploadProject = function() {
        if ($scope.UploadProjectForm.$invalid) {
          modalService.informError([{message: 'Please fill in all the required project fields.'}]);
          return false;
        } else {
          var fileName = $scope.projectParams.file.name;
          var fileExt = fileName.substr(fileName.lastIndexOf('.') + 1, fileName.length);
          if (fileExt !== 'prj') {
            modalService.informError([{message: 'Please upload an Optima project file. This should have the file extension .prj. ' +
            'If you are trying to upload a spreadsheet, use the "Upload Optima spreadsheet" option instead.'}]);
            return false;
          } else {
            $upload.upload({
              url: '/api/project/data',
              fields: {name: $scope.projectParams.name},
              file: $scope.projectParams.file
            }).success(function (data, status, headers, config) {
              var name = data['name'];
              var projectId = data['id'];
              console.log('upload', data);
              activeProject.setActiveProjectFor(name, projectId, UserManager.data);
              $state.go('home');
            });
          }
        }
      };

      $scope.projectExists = function() {
        var projectNames = _.pluck(projects.data.projects, 'name');
        var exists = _(projectNames).contains($scope.projectParams.name);
        $scope.UploadProjectForm.ProjectName.$setValidity("projectExists", !exists);
        return exists;
      };
    }
  );

});
