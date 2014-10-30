define(['./module'], function (module) {
  'use strict';

  module.controller('OptimizationObjectivesController', function ($scope, $http) {

    $scope.defineOptimization = function () {
      $http.post('/api/analysis/optimisation/define', {})
        .success(function (response) {
          console.log('post to /api/analysis/optimisation/define is done!', response);
        })
    };
  });

});
