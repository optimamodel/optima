define(['./module', "underscore"], function (module, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $window) {

    $scope.createProject = function() {

      $window.open('/api/project/create/'+ $scope.projectParams.name + 
        "?params=" + JSON.stringify(_($scope.projectParams).omit("name")));
    }

  });

});
