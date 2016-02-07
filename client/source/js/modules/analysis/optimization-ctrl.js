define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  /**
   * Defines & validates objectives, parameters & constraints to run, display &
   * save optimization results.
   */
  module.controller('AnalysisOptimizationController', function ($scope, $http, modalService, activeProject) {

    if (!activeProject.data.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $scope.missingData = true;
      return;
    }


    $scope.state = {
      activeProject: activeProject.data,
      objectives: {}
    };

    $http.get('/api/project/' + $scope.state.activeProject.id + '/optimizations').
      success(function (response) {
        console.log('response', response);
      });


  });
});
