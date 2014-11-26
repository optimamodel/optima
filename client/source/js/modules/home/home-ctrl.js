define(['./module'], function (module) {
  'use strict';

  module.controller('HomeController', function ($scope, project) {

    // initialize data for the template
    var initialize= function() {
      $scope.project = project;
    };

    initialize();

  });
});
