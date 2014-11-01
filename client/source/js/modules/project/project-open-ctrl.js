define(['./module'], function (module) {
  'use strict';

  module.controller('ProjectOpenController', function ($scope, projects) {
    $scope.projects = projects.projects;
  });

});
