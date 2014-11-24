define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ProjectOpenController', function ($scope, $http, activeProject, localStorage, projects) {
    $scope.projects = _(projects.projects).map(function (fileName) {
      return fileName.split('.')[0];
    });

    $scope.open = function (name) {
      $http.get('/api/project/open/' + name)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
            return;
          }
          activeProject.setValue(name);
        });
    };

    $scope.delete = function (name) {
      $http.delete('/api/project/delete/' + name)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
            return;
          }

          $scope.projects.splice($scope.projects.indexOf(name), 1);
        })
        .error(function () {
          alert('Could not remove the project')
        });
    };
  });

});
