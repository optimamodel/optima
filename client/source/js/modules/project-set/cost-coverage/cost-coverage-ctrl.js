define(['./../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http, $state, activeProject, modalService, projectApiService) {

    var vm = this;

    vm.openProject = activeProject.data;

    // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
    if (!vm.openProject.has_data) {
      modalService.inform(
        function () {
        },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $state.go('project.open');
      return;
    }

    // Initializing tabs and setting default tab
    vm.activeTab = 'cost';
    vm.tabs = [{
      name: 'Define cost functions',
      slug: 'cost'
    }, {
      name: 'Define outcome functions',
      slug: 'outcome'
    }, {
      name: 'View summary',
      slug: 'summary'
    }];

    // Fetch list of program-set for open-project from BE
    $http.get('/api/project/' + vm.openProject.id + '/progsets')
      .success(function (response) {
        if (response.progsets) {
          vm.programSetList = response.progsets;
        }
      });

    // Fetch list of parameter-set for open-project from BE
    $http.get('/api/project/' + vm.openProject.id + '/parsets').success(function (response) {
      vm.parsets = response.parsets;
    });

    // Population program drop-down for selected program-set
    vm.populateProgramDropdown = function() {
      if (vm.selectedProgramSet) {
        vm.programs = _.filter(vm.selectedProgramSet.programs, function(program) {
          return program.parameters && program.parameters.length > 0;
        });
      }
    };

    // todo: move code below to separate controller for outcome
    vm.years = [{
      /* ToDo: replace with api data */
      id: 1
    }];

    /* VM functions */
    var fakeParams = [
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
    ];
    vm.fakeParams = angular.copy(fakeParams);

    vm.post = {};
    vm.addYear = addYear;
    vm.selectTab = selectTab;
    vm.deleteYear = deleteYear;
    vm.submit = submit;
    vm.changeParameter = changeParameter;

    /* Function definitions */

    function changeParameter(){
      vm.post = {};
      vm.TableForm.$setPristine();
    }

    function submit() {
      if (vm.TableForm.$invalid) {
        console.error('form is invalid!');
        return false;
      }

      console.log('submitting', vm.post);
    }

    function deleteYear(yearIndex) {
      vm.years = _.reject(vm.years, function (year, index) {
        return index === yearIndex
      });
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function addYear() {
      vm.years.push({id: _.random(1, 10000)});
      /* ToDo: replace with api data */
    }

  });

});
