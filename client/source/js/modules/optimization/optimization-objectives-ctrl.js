define(['./module'], function (module) {
  'use strict';

  module.controller('OptimizationObjectivesController', function ($scope, $http) {

    $scope.params = {
      forecast: {},
      optimize: {},
      minimize: {}
    };

    $scope.submit = function (type) {
      $http.post('/api/analysis/optimisation/define/' + type, $scope.params[type])
        .success(function (response) {
          console.log('post to /api/analysis/optimisation/define is done!', response);
        })
    };
  });

});
