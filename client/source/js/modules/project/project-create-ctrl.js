define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $window) {

    $scope.createProject = function() {
      $window.open('/api/data/download/ '+ $scope.projectName);
    }

  });

});
