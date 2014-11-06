define(['./module'], function (module) {
  'use strict';

  module.controller('HomeController', function ($scope, activeProject) {
    $scope.projectName = activeProject.name;
  });
});
