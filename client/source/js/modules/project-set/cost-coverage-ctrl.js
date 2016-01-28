define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http,
    $state, activeProject, modalService, projectApiService) {

    $scope.state = {
      activeTab: 'defineOutcomeFunctions'
    };

    var openProject = activeProject.data;

    // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
    if (!openProject.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $state.go('project.open')
      return;
    }


    $scope.state.fakeParams = [
      {
        name: 'First'
      },
      {
        name: 'Second'
      },
      {
        name: 'Third'
      }
    ]

    $scope.changeParameter = function (newParameter) {
      console.log('newParameter', $scope.state.selectedParameter);
    }

    $http.get('/api/project/' + openProject.id + '/progsets')
      .success(function (response) {
        if(response.progsets) {
          $scope.state.programSetList = response.progsets;
        }
      });

    $scope.populateProgramDropdown = function() {
      $scope.state.programs = $scope.state.selectedProgramSet.programs;
    };

    $http.get('/api/project/' + openProject.id + '/parsets').
      success(function (response) {
        $scope.state.parsets = response.parsets;
      });
  });


});
