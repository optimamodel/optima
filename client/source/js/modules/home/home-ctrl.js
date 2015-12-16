define(['./module', 'underscore'], function (module) {
  'use strict';

  module.controller('HomeController', function ($scope, project) {

    // initialize data for the template
    var initialize= function() {
      $scope.project = project.data;

      if ($scope.project) {
        $scope.project.creation_time = Date.parse($scope.project.creation_time);
        $scope.project.updated_time = Date.parse($scope.project.updated_time);
        $scope.project.data_upload_time = Date.parse($scope.project.data_upload_time);
      }
    };

    initialize();

  });
});
