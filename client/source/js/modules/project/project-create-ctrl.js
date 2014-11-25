define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $state, $modal, activeProject) {

    $scope.projectParams = {
      name: ''
    };

    $scope.populations = [
      {
        active: false, internal_name: "FSW", short_name: "FSW", name: "Female sex workers",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: true, sex_work_client: false, female: true, male: false
      },
      {
        active: false, internal_name: "CSW", short_name: "Clients", name: "Clients of sex workers",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: true, female: false, male: true
      },
      {
        active: false, internal_name: "MSM", short_name: "MSM", name: "Men who have sex with men",
        heterosexual: false, homosexual: true, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: true
      },
      {
        active: false, internal_name: "TI", short_name: "Transgender", name: "Transgender individuals",
        heterosexual: false, homosexual: true, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: false
      },
      {
        active: false, internal_name: "PWID", short_name: "PWID", name: "People who inject drugs",
        heterosexual: true, homosexual: false, injects_drugs: true, sex_work_provider: false, sex_work_client: false, female: false, male: false
      },
      {
        active: false, internal_name: "MWID", short_name: "Male PWID", name: "Males who inject drugs",
        heterosexual: true, homosexual: false, injects_drugs: true, sex_work_provider: false, sex_work_client: false, female: false, male: true
      },
      {
        active: false, internal_name: "FWID", short_name: "Female PWID", name: "Females who inject drugs",
        heterosexual: true, homosexual: false, injects_drugs: true, sex_work_provider: false, sex_work_client: false, female: true, male: false
      },
      {
        active: false, internal_name: "CHILD", short_name: "Children", name: "Children (2-15)",
        heterosexual: false, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: false
      },
      {
        active: false, internal_name: "INF", short_name: "Infants", name: "Infants (0-2)",
        heterosexual: false, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: false
      },
      {
        active: false, internal_name: "OM15_49", short_name: "Males 15-49", name: "Other males (15-49)",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: true
      },
      {
        active: false, internal_name: "OF15_49", short_name: "Females 15-49", name: "Other females (15-49)",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: true, male: false
      },
      {
        active: false, internal_name: "OM", short_name: "Other males", name: "Other males [enter age]",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: false, male: true
      },
      {
        active: false, internal_name: "OF", short_name: "Other females", name: "Other females [enter age]",
        heterosexual: true, homosexual: false, injects_drugs: false, sex_work_provider: false, sex_work_client: false, female: true, male: false
      }
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
      document.getElementById('createForm').action = $scope.formAction;
      document.getElementById('params').value = $scope.formParams;
      document.getElementById('createForm').submit();

      // update active project
      activeProject.setValue($scope.projectParams.name);

      $state.go('home');

      return true;
    };

  });

});
