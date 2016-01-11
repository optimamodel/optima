define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateOrEditController', function ($scope, $state, $modal,
    $timeout, $http, activeProject, defaultsResponse,
    UserManager, modalService,projects, projectApiService, info) {

    var allProjects = projects.data.projects;

    $scope.projectExists = function () {
      return _.some(allProjects, function (project) {
        return $scope.projectParams.name === project.name && $scope.projectParams.id !== project.id;
      });
    };

    $scope.projectParams = {
      name: ''
    };
    $scope.editParams = {
      isEdit: false,
      canUpdate: true
    };

    $scope.projectInfo = info ? info.data : void 0;

    var availableDefaults = defaultsResponse.data;

    $scope.submit = "Create project & Optima template";
    $scope.populations = availableDefaults.populations;
    $scope.categories = availableDefaults.categories;

    function isEditMode(){
      return $state.current.name == "project.edit";
    }

    function findByName(arr,obj){
        return _.findWhere(arr, {short_name: obj.short_name});
    }

    if (isEditMode()) {
      // change submit button name
      $scope.submit = "Save project & Optima template";

      $scope.editParams.isEdit = true;
      $scope.oldProjectName =  $scope.projectInfo.name;

      if (activeProject.isSet()) {
        $scope.projectParams.id = $scope.projectInfo.id;
        $scope.projectParams.name = $scope.oldProjectName;
        $scope.projectParams.datastart = $scope.projectInfo.dataStart;
        $scope.projectParams.dataend = $scope.projectInfo.dataEnd;
      }

      $scope.populations = $scope.populations.concat(_($scope.projectInfo.populations).filter(function (population) {
        return !findByName($scope.populations, population);
      }));

      _($scope.populations).each(function(population){
        var source = findByName($scope.projectInfo.populations, population);
        if (source) {
          population.active = true;
          _.extend(population, source);
        }
      });

    }

    // Helper function to open a population modal
    var openPopulationModal = function (population) {
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

    /*
    * Returns true of the two provided arrays are identic
    */
    var areEqualArrays = function(arrayOne, arrayTwo) {
      return _(arrayOne).every(function(element, index) {
        return element === arrayTwo[index];
      });
    };

    /*
     * Returns a collection of entries where all non-active antries are filtered
     * out and the active attribute is removed from each of these entries.
     */
    var toCleanArray = function (collection) {
      return _(collection).chain()
        .where({ active: true })
        .map(function (item) {
          var cl = _(item).omit(['active', '$$hashKey']);
          if (cl.parameters) {
            cl.parameters = _(cl.parameters).chain()
              .where({ active: true })
              .map(function (param) {
                return _(param).omit(['active', '$$hashKey']);
              })
              .value();
            if (cl.parameters === 0) delete cl.parameters;
          }
          return cl;
        })
        .value();
    };

    $scope.prepareCreateOrEditForm = function () {

      const populationSelected = _.find($scope.populations, function(population) {
        return population.active === true;
      });

      if ($scope.CreateOrEditProjectForm.$invalid || !populationSelected) {
        modalService.informError([{message: 'Please fill in all the required project fields'}]);
        return false;
      }

      var selectedPopulations = toCleanArray($scope.populations);

      if ( $state.current.name == "project.edit" ) {
        var message;
        if ( !angular.equals( selectedPopulations,$scope.projectInfo.populations ) ) {
          $scope.editParams.canUpdate = selectedPopulations.length == $scope.projectInfo.populations.length;
          message = 'You have made changes to populations. All existing data will be lost. Would you like to continue?';
          if ($scope.editParams.canUpdate) {
            message = 'You have changed some population parameters. Your original data can be reapplied, but you will have to redo the calibration and analysis. Would you like to continue?';
          }
          modalService.confirm(
            function (){ continueSubmitForm( selectedPopulations ); },
            function (){},
            'Yes, save this project',
            'No',
            message,
            'Save Project?'
          );
        } else {
          message = 'No parameters have been changed. Do you intend to reload the original data and start from scratch?';
          modalService.confirm(
            function (){ continueSubmitForm( selectedPopulations ); },
            function (){},
            'Yes, reload this project',
            'No',
            message,
            'Reload project?'
          );
        }
      } else {
        continueSubmitForm( selectedPopulations );
      }
    };

    // handle another function to continue to submit form
    // since the confirm modal is async and doesn't wait for user's response
    var continueSubmitForm = function( selectedPopulations ) {
      var form = {};
      var params;

      var promise;
      if ($scope.editParams.isEdit) {
        params = angular.copy($scope.projectParams);
        params.populations = selectedPopulations;
        promise = projectApiService.updateProject($scope.projectInfo.id, params);
      } else {
        params = angular.copy($scope.projectParams);
        params.populations = selectedPopulations;
        promise = projectApiService.createProject(params);
      }

      promise
        .success(function (response, status, headers, config) {
            var newProjectId = headers()['x-project-id'];
            var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            saveAs(blob, ($scope.projectParams.name + '.xlsx'));
                  // update active project
            activeProject.setActiveProjectFor($scope.projectParams.name, newProjectId, UserManager.data);
            $state.go('home');
          });
    };

  });

});
