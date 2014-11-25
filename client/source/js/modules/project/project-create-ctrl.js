define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $state, $modal,
    activeProject, DEFAULT_PROGRAMS, DEFAULT_POPULATIONS) {

    $scope.projectParams = {
      name: ''
    };

    $scope.populations = DEFAULT_POPULATIONS;
    $scope.programs = DEFAULT_PROGRAMS;

    // Helper function to open a population modal
    var openPopulationModal = function(population) {
      return $modal.open({
        templateUrl: 'js/modules/project/create-population-modal.html',
        controller: 'ProjectCreatePopulationModalController',
        resolve: {
          population: function () {
            return population;
          }
        }
      });
    };

    /*
    * Creates a new population and opens a modal for editing.
    *
    * The entry is only pushed to the list of populations if editing in the modal
    * ended with a successful save.
    */
    $scope.openAddPopulationModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var population = {};

      return openPopulationModal(population).result.then(
        function (newPopulation) {
          $scope.populations.push(newPopulation);
        }
      );
    };

    /*
    * Opens a modal for editing an existing population.
    */
    $scope.openEditPopulationModal = function ($event, population) {
      if ($event) {
        $event.preventDefault();
      }

      return openPopulationModal(population).result.then(
        function (newPopulation) {
          _(population).extend(newPopulation);
        }
      );
    };

    /*
    * Makes a copy of an existing population and opens a modal for editing.
    *
    * The entry is only pushed to the list of populations if editing in the
    * modal ended with a successful save.
    */
    $scope.copyPopulationAndOpenModal = function ($event, existingPopulation) {
      if ($event) {
        $event.preventDefault();
      }
      var population = angular.copy(existingPopulation);

      return openPopulationModal(population).result.then(
        function (newPopulation) {
          $scope.populations.push(newPopulation);
        }
      );
    };

    // Helper function to open a program modal
    var openProgramModal = function(program) {
      return $modal.open({
        templateUrl: 'js/modules/project/create-program-modal.html',
        controller: 'ProjectCreateProgramModalController',
        resolve: {
          program: function () {
            return program;
          }
        }
      });
    };

    /*
    * Creates a new program and opens a modal for editing.
    *
    * The entry is only pushed to the list of programs if editing in the modal
    * ended with a successful save.
    */
    $scope.openAddProgramModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var program = {};

      return openProgramModal(program).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

    /*
    * Opens a modal for editing an existing program.
    */
    $scope.openEditProgramModal = function ($event, program) {
      if ($event) {
        $event.preventDefault();
      }

      return openProgramModal(program).result.then(
        function (newProgram) {
          _(program).extend(newProgram);
        }
      );
    };

    /*
     * Makes a copy of an existing program and opens a modal for editing.
     *
     * The entry is only pushed to the list of programs if editing in the modal
     * ended with a successful save.
     */
    $scope.copyProgram = function ($event, existingProgram) {
      if ($event) {
        $event.preventDefault();
      }
      var program = angular.copy(existingProgram);

      return openProgramModal(program).result.then(
        function (newProgram) {
          $scope.programs.push(newProgram);
        }
      );
    };

    /*
     * Returns a collection of entries where all non-active antries are filtered
     * out and the active attribute is removed from each of these entries.
     */
    var toCleanArray = function (collection) {
      return _(collection).chain()
        .where({ active: true })
        .map(function (item) {
          return _(item).omit(['active', '$$hashKey']);
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
