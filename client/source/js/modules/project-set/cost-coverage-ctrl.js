define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http, $state, activeProject, modalService, projectApiService) {

    var vm = this;
    var openProject = activeProject.data;

    /* VM vars */
    vm.activeTab = 'outcome';
    vm.fakeParams = [
      {
        name: 'First'
      },
      {
        name: 'Second',
        coverage: true
      },
      {
        name: 'Third'
      }
    ]
    vm.post = {}
    vm.tabs = [
      {
        name: 'Define cost functions',
        slug: 'cost'
      },
      {
        name: 'Define outcome functions',
        slug: 'outcome'
      },
      {
        name: 'View summary',
        slug: 'summary'
      }
    ]
    vm.selectedParameter = vm.fakeParams[1]
    vm.years = [{}]

    /* VM functions */
    vm.populateProgramDropdown = populateProgramDropdown;
    vm.changeParameter = changeParameter;
    vm.addYear = addYear;
    vm.selectTab = selectTab;
    vm.deleteYear = deleteYear;

    function deleteYear(yearIndex) {
      vm.years = _.reject(vm.years, function (year, index) {
        return index === yearIndex
      });
    }

    /* Function definitions */

    function populateProgramDropdown() {
      vm.programs = vm.selectedProgramSet.programs;
    };

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function changeParameter(newParameter) {
      console.log('newParameter', vm.selectedParameter);
    }

    function addYear() {
      vm.years.push({})
    }

    /* Initialize */

    // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
    if (!openProject.has_data) {
      modalService.inform(
        function () {
        },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $state.go('project.open')
      return;
    }

    $http.get('/api/project/' + openProject.id + '/progsets')
      .success(function (response) {
        if (response.progsets) {
          vm.programSetList = response.progsets;
        }
      });

    $http.get('/api/project/' + openProject.id + '/parsets').success(function (response) {
      vm.parsets = response.parsets;
    });

    $scope.$watch(function () {
      return vm.post
    }, function () {
      console.log('post is', vm.post);
    }, true);

  });


});
