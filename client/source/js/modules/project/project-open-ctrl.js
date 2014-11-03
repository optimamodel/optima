define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ProjectOpenController', function ($scope, $http, projects) {
    $scope.projects = _(projects.projects).map(function (fileName) {
      return fileName.split('.')[0];
    });

    $scope.open = function (name) {
      $http.get('/api/project/open/' + name)
        .success(function (response) {
          if (response && response.status === 'NOK') {
            alert(response.reason);
          }
        })
    }
  });

});
