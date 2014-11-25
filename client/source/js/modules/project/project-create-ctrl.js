define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $state, $modal, activeProject) {

    $scope.projectParams = {
      name: ''
    };

    $scope.populations = [
      {
        active: false, internal_name: "FSW", short_name: "FSW", name: "Female sex workers",
        hetero: true, homo: false, injects: false, sexworker: true, client: false, female: true, male: false
      },
      {
        active: false, internal_name: "CSW", short_name: "Clients", name: "Clients of sex workers",
        hetero: true, homo: false, injects: false, sexworker: false, client: true, female: false, male: true
      },
      {
        active: false, internal_name: "MSM", short_name: "MSM", name: "Men who have sex with men",
        hetero: false, homo: true, injects: false, sexworker: false, client: false, female: false, male: true
      },
      {
        active: false, internal_name: "TI", short_name: "Transgender", name: "Transgender individuals",
        hetero: false, homo: true, injects: false, sexworker: false, client: false, female: false, male: false
      },
      {
        active: false, internal_name: "PWID", short_name: "PWID", name: "People who inject drugs",
        hetero: true, homo: false, injects: true, sexworker: false, client: false, female: false, male: false
      },
      {
        active: false, internal_name: "MWID", short_name: "Male PWID", name: "Males who inject drugs",
        hetero: true, homo: false, injects: true, sexworker: false, client: false, female: false, male: true
      },
      {
        active: false, internal_name: "FWID", short_name: "Female PWID", name: "Females who inject drugs",
        hetero: true, homo: false, injects: true, sexworker: false, client: false, female: true, male: false
      },
      {
        active: false, internal_name: "CHILD", short_name: "Children", name: "Children (2-15)",
        hetero: false, homo: false, injects: false, sexworker: false, client: false, female: false, male: false
      },
      {
        active: false, internal_name: "INF", short_name: "Infants", name: "Infants (0-2)",
        hetero: false, homo: false, injects: false, sexworker: false, client: false, female: false, male: false
      },
      {
        active: false, internal_name: "OM15_49", short_name: "Males 15-49", name: "Other males (15-49)",
        hetero: true, homo: false, injects: false, sexworker: false, client: false, female: false, male: true
      },
      {
        active: false, internal_name: "OF15_49", short_name: "Females 15-49", name: "Other females (15-49)",
        hetero: true, homo: false, injects: false, sexworker: false, client: false, female: true, male: false
      },
      {
        active: false, internal_name: "OM", short_name: "Other males", name: "Other males [enter age]",
        hetero: true, homo: false, injects: false, sexworker: false, client: false, female: false, male: true
      },
      {
        active: false, internal_name: "OF", short_name: "Other females", name: "Other females [enter age]",
        hetero: true, homo: false, injects: false, sexworker: false, client: false, female: true, male: false
      }
    ];

    $scope.programs = [
      {
        active: false, internal_name: "COND", short_name: "Condoms",
        name: "Condom promotion and distribution", saturating: true
      },
      {
        active: false, internal_name: "SBCC", short_name: "SBCC",
        name: "Social and behavior change communication", saturating: true
      },
      {
        active: false, internal_name: "STI", short_name: "STI",
        name: "Diagnosis and treatment of sexually transmitted infections", saturating: true
      },
      {
        active: false, internal_name: "VMMC", short_name: "VMMC",
        name: "Voluntary medical male circumcision", saturating: false
      },
      {
        active: false, internal_name: "CT", short_name: "Cash transfers",
        name: "Cash transfers for HIV risk reduction", saturating: true
      },
      {
        active: false, internal_name: "FSWP", short_name: "FSW programs",
        name: "Programs for female sex workers and clients", saturating: true
      },
      {
        active: false, internal_name: "MSMP", short_name: "MSM programs",
        name: "Programs for men who have sex with men", saturating: true
      },
      {
        active: false, internal_name: "PWIDP", short_name: "PWID programs",
        name: "Programs for people who inject drugs", saturating: true
      },
      {
        active: false, internal_name: "OST", short_name: "OST",
        name: "Opiate substitution therapy", saturating: false
      },
      {
        active: false, internal_name: "NSP", short_name: "NSP",
        name: "Needle-syringe program", saturating: true
      },
      {
        active: false, internal_name: "PREP", short_name: "PrEP",
        name: "Pre-exposure prophylaxis/microbicides", saturating: true
      },
      {
        active: false, internal_name: "PEP", short_name: "PEP",
        name: "Post-exposure prophylaxis", saturating: true
      },
      {
        active: false, internal_name: "HTC", short_name: "HTC",
        name: "HIV testing and counseling", saturating: true
      },
      {
        active: false, internal_name: "ART", short_name: "ART",
        name: "Antiretroviral therapy", saturating: false
      },
      {
        active: false, internal_name: "PMTCT", short_name: "PMTCT",
        name: "Prevention of mother-to-child transmission", saturating: false
      },
      {
        active: false, internal_name: "CARE", short_name: "Other care",
        name: "Other HIV care", saturating: false
      },
      {
        active: false, internal_name: "OVC", short_name: "OVC",
        name: "Orphans and vulnerable children", saturating: false
      },
      {
        active: false, internal_name: "MGMT", short_name: "MGMT",
        name: "Management", saturating: false
      },
      {
        active: false, internal_name: "HR", short_name: "HR",
        name: "HR and training", saturating: false
      },
      {
        active: false, internal_name: "ENV", short_name: "ENV",
        name: "Enabling environment", saturating: false
      },
      {
        active: false, internal_name: "SP", short_name: "SP",
        name: "Social protection", saturating: false
      },
      {
        active: false, internal_name: "MESR", short_name: "M&E",
        name: "Monitoring, evaluation, surveillance, and research", saturating: false
      },
      {
        active: false, internal_name: "INFR", short_name: "INFR",
        name: "Health infrastructure", saturating: false
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
            return {};
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
            return {};
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
