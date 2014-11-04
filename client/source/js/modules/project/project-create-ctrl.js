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

    $scope.programs = [
      {name: 'HIV testing & counseling', active: false},
      {name: 'Female sex workers', active: false},
      {name: 'Men who have sex with men', active: false},
      {name: 'Antiretroviral therapy', active: false},
      {name: 'Prevention of mother-to-child transmission', active: false},
      {name: 'Behavior change & communication', active: false},
      {name: 'Needle-syringe program', active: false},
      {name: 'Opiate substitution therapy', active: false},
      {name: 'Cash transfers', active: false}
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

    var addItemTo = function (collection, itemName) {
      collection.push({
        name: itemName,
        active: true
      });
    };

    $scope.addPopulation = function ($event) {
      $event.preventDefault();
      addItemTo($scope.populations, $scope.newPopulation);
      $scope.newPopulation = '';
    };

    $scope.addProgram = function ($event) {
      $event.preventDefault();
      addItemTo($scope.programs, $scope.newProgram);
      $scope.newProgram = '';
    };

    var toNamesArray = function (collection) {
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
      params.programs = toNamesArray($scope.programs);
      params.populations = toNamesArray($scope.populations);

      $scope.formAction = '/api/project/create/' + $scope.projectParams.name;
      $scope.formParams = JSON.stringify(params);

      // according to documentation it should have been working without this line, but no cigar
      // https://docs.angularjs.org/api/ng/directive/ngSubmit
      document.getElementById('createForm').submit();

      return true;
    };

  });

});
