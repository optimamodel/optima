define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $modal) {

    $scope.projectParams = {
      name: ''
    };

    $scope.populations = [
      { name: 'Female sex workers', acronym: 'FSW', active: false },
      { name: 'Clients of sex workers', acronym: 'CSW', active: false },
      { name: 'Men who have sex with men', acronym: 'MSM', active: false },
      { name: 'Males who inject drugs', acronym: 'MID', active: false },
      { name: 'Females who inject drugs', acronym: 'FID', active: false },
      { name: 'Transgender individuals', acronym: 'TI', active: false },
      { name: 'Children (2-15)', acronym: 'C215', active: false },
      { name: 'Infants (0-2)', acronym: 'I02', active: false },
      { name: 'Other males [open text box to enter age range]', acronym: 'OM', active: false },
      { name: 'Other females [open text box to enter age range]', acronym: 'OF', active: false }
    ];

    $scope.programs = [];

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

      return true;
    };

  });

});
