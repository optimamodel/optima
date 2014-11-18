define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $state, $modal, activeProject) {

    $scope.projectParams = {
      name: ''
    };

    $scope.populations = [
      { name: 'Female sex workers', acronym: 'FSW', active: false },
      { name: 'Clients of sex workers', acronym: 'CSW', active: false },
      { name: 'Men who have sex with men', acronym: 'MSM', active: false },
      { name: 'People who inject drugs', acronym: 'PWID', active: false },
      { name: 'Males who inject drugs', acronym: 'MWID', active: false },
      { name: 'Females who inject drugs', acronym: 'FWID', active: false },
      { name: 'Transgender individuals', acronym: 'TG', active: false },
      { name: 'Children (2-15)', acronym: 'CHLD', active: false },
      { name: 'Infants (0-2)', acronym: 'INF', active: false },
      { name: 'Other males (15-49)', acronym: 'OM15-49', active: false },
      { name: 'Other females (15-49)', acronym: 'OF15-49', active: false },
      { name: 'Other males [enter age]', acronym: 'OM', active: false },
      { name: 'Other females [enter age]', acronym: 'OF', active: false }
    ];

    $scope.programs = [
        {
            name: 'Behavior change and communication',
            acronym: 'BCC',
            indicators: [
                { name: 'Condom use among general population males and females', active: true },
                { name: 'VMMC uptake and ART adherence', active: false },
                { name: 'Uptake of other programs and services', active: false },
                { name: 'Linkages to biomedical services', active: true }
            ]
        },
        {
            name: 'HIV testing and counseling',
            acronym: 'HTC',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Programs for female sex workers and their clients',
            acronym: 'PFSW',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Programs for men who have sex with men',
            acronym: 'PMSM',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Needle-syringe program',
            acronym: 'NSP',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Opiate substitution therapy',
            acronym: 'OST',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Sexually transmitted infections',
            acronym: 'STI',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Prevention of mother-to-child transmission',
            acronym: 'PMTCT',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Voluntary medical male circumcision',
            acronym: 'VMMC',
            indicators: [
                { name: 'Relative increase in condom use and testing in general populations', active: false },
                { name: 'VMMC uptake and ART adherence', active: true },
                { name: 'Uptake of other programs and services', active: true },
                { name: 'Linkages to biomedical services', active: false }
            ]
        },
        {
            name: 'Antiretroviral therapy',
            acronym: 'ART',
            indicators: [
                {
                    name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
                    active: true
                }
            ]
        }

    ];

    $scope.openAddPopulationModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }

      return $modal.open({
        templateUrl: 'js/modules/project/create-population-modal.html',
        controller: 'ProjectCreatePopulationModalController',
        resolve: {
          population: function () {
            return {
              sex: 'male'
            };
          }
        }
      }).result.then(
        function (newPopulation) {
          newPopulation.active = true;
          $scope.populations.push(newPopulation);
        });
    };

    $scope.openEditPopulationModal = function ($event, population) {
      if ($event) {
        $event.preventDefault();
      }

      return $modal.open({
        templateUrl: 'js/modules/project/create-population-modal.html',
        controller: 'ProjectCreatePopulationModalController',
        resolve: {
          population: function () {
            return population;
          }
        }
      }).result.then(
        function (newPopulation) {
          population.active = true;
          _(population).extend(newPopulation);
        });
    };

    $scope.openAddProgramModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }

      return $modal.open({
        templateUrl: 'js/modules/project/create-program-modal.html',
        controller: 'ProjectCreateProgramModalController',
        resolve: {
          program: function () {
            return null;
          }
        }
      }).result.then(
        function (newProgram) {
          newProgram.active = true;
          $scope.programs.push(newProgram);
        });
    };

    $scope.openEditProgramModal = function ($event, program) {
      if ($event) {
        $event.preventDefault();
      }

      return $modal.open({
        templateUrl: 'js/modules/project/create-program-modal.html',
        controller: 'ProjectCreateProgramModalController',
        resolve: {
          program: function () {
            return program;
          }
        }
      }).result.then(
        function (newProgram) {
          program.active = true;
          _(program).extend(newProgram);
        });
    };

    var toCleanArray = function (collection) {
      return _(collection).chain()
        .where({ active: true })
        .map(function (item) {
          return _(item).omit(['active', '$$hashKey'])
        })
        .value();
    };

    $scope.prepareCreateForm = function () {
      if ($scope.CreateProjectForm.$invalid) {
        alert('Please fill in all the required project fields');
        return false;
      }

      var params = _($scope.projectParams).omit('name');
      params.programs = toCleanArray($scope.programs);
      _(params.programs).map(function (item) {
        item.indicators = toCleanArray(item.indicators);
        return item;
      });
      params.populations = toCleanArray($scope.populations);

      $scope.formAction = '/api/project/create/' + $scope.projectParams.name;
      $scope.formParams = JSON.stringify(params);

      // according to documentation it should have been working without this line, but no cigar
      // https://docs.angularjs.org/api/ng/directive/ngSubmit
      document.getElementById('createForm').submit();

      // update active project
      activeProject.setValue($scope.projectParams.name);

      $state.go('home');

      return true;
    };

  });

});
