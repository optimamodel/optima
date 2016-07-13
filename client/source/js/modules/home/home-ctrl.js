define(['./module', 'underscore'], function (module) {
  'use strict';

  module.controller('HomeController', function ($scope, project) {

    // initialize data for the template
    var initialize= function() {

      console.log(project);
      if (project && project.data) {
        $scope.project = project.data;
        $scope.project.creationTime = Date.parse($scope.project.creationTime);
        $scope.project.updatedTime = Date.parse($scope.project.updatedTime);
        $scope.project.dataUploadTime = Date.parse($scope.project.dataUploadTime);
      }
    };

    initialize();

  });
});
