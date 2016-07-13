define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateOrEditController', function (
      $scope, $state, $modal, $timeout, $http, activeProject, populations,
      UserManager, modalService, projects, projectApiService, info) {

    function initialize() {
      $scope.allProjects = projects.data.projects;
      $scope.projectParams = {
        name: ''
      };
      $scope.editParams = {
        isEdit: false,
        canUpdate: true
      };

      $scope.projectInfo = info ? info.data : void 0;

      $scope.submit = "Create project & Optima template";
      $scope.populations = populations.data.populations;
      console.log('default populations', $scope.populations);

      if (isEditMode()) {
        // change submit button name
        $scope.submit = "Save project & Optima template";

        $scope.editParams.isEdit = true;

        if (activeProject.isSet()) {
          $scope.projectParams.id = $scope.projectInfo.id;
          $scope.projectParams.name = $scope.projectInfo.name;
          $scope.projectParams.datastart = $scope.projectInfo.dataStart;
          $scope.projectParams.dataend = $scope.projectInfo.dataEnd;
        }

        $scope.populations = $scope.populations.concat(_($scope.projectInfo.populations).filter(function(projectPopulation) {
          return !_.find($scope.populations, function(population) {
            return projectPopulation.name === population.name && projectPopulation.short === population.short;
          });
        }));

        _($scope.populations).each(function(population) {
          var source = findByName($scope.projectInfo.populations, population);
          if (source) {
            population.active = true;
            _.extend(population, source);
          }
        });

      }
    }

    $scope.projectExists = function () {
      return _.some($scope.allProjects, function (project) {
        return $scope.projectParams.name === project.name && $scope.projectParams.id !== project.id;
      });
    };

    $scope.invalidName = function() {
      return !$scope.projectParams.name;
    };

    $scope.invalidDataStart = function() {
      if ($scope.projectParams.datastart) {
        var datastart = parseInt($scope.projectParams.datastart)
        return datastart < 1900 || 2100 < datastart;
      }
      return !$scope.projectParams.datastart; 
    };

    $scope.invalidDataEnd = function() {
      if ($scope.projectParams.dataend) {
        var dataend = parseInt($scope.projectParams.dataend)
        if (dataend < 1900 || 2100 < dataend) {
          return true;
        };
        if ($scope.invalidDataStart()) {
          return false;
        }
        var datastart = parseInt($scope.projectParams.datastart)
        return dataend <= datastart;
      }
      return !$scope.projectParams.dataend;  
    };

    $scope.invalidPopulationSelected = function() {
      var result = _.find($scope.populations, function(population) {
        return population.active === true;
      });
      return !result;
    };

    function isEditMode(){
      return $state.current.name == "project.edit";
    }

    function findByName(arr,obj){
        return _.findWhere(arr, {short: obj.short, name: obj.name});
    }

    function openPopulationModal(population) {
      return $modal.open({
        templateUrl: 'js/modules/project/create-population-modal.html',
        controller: 'ProjectCreatePopulationModalController',
        resolve: {
          populations: function(){
            return populations.data.populations;
          },
          population: function(){
            return population;
          }
        }
      });
    }

    /**
     * Opens a model to create population, push on successful save
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

    /**
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

    /**
     * Copies existing population, push on successful save
     */
    $scope.copyPopulationAndOpenModal = function ($event, existingPopulation) {
      if ($event) {
        $event.preventDefault();
      }
      var population = angular.copy(existingPopulation);
      population.name = population.name + ' copy';
      population.short = population.short + ' copy';

      return openPopulationModal(population).result.then(
        function (newPopulation) {
          $scope.populations.push(newPopulation);
        }
      );
    };

    /**
     * Returns a collection of active entries, with active & $$hasKey removed
     */
    function toCleanArray(collection) {
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
    }

    function continueSubmitForm( selectedPopulations ) {
      var params, promise;
      if ($scope.editParams.isEdit) {
        params = angular.copy($scope.projectParams);
        params.populations = selectedPopulations;
        promise = projectApiService.updateProject(
            $scope.projectInfo.id, params);
      } else {
        params = angular.copy($scope.projectParams);
        params.populations = selectedPopulations;
        promise = projectApiService.createProject(params);
      }
      promise
        .success(function (response, status, headers, config) {
            var newProjectId = headers()['x-project-id'];
            var blob = new Blob(
                [response],
                { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            saveAs(blob, ($scope.projectParams.name + '.xlsx'));
            // update active project
            activeProject.setActiveProjectFor(
                $scope.projectParams.name, newProjectId, UserManager.data);
            $state.go('home');
        });
    }

    $scope.prepareCreateOrEditForm = function () {
      var errors = [];

      if ($scope.invalidName()) {
        errors.push({message: 'Enter a project name'});
      }
      if ($scope.invalidDataStart()) {
        errors.push({message: 'Enter a first year'});
      }
      if ($scope.invalidDataEnd()) {
        errors.push({message: 'Enter a final year'});
      }
      if ($scope.invalidPopulationSelected()) {
        errors.push({message: 'Select at least one population'});
      }

      if ($scope.CreateOrEditProjectForm.$invalid || $scope.invalidPopulationSelected()) {
        modalService.informError(errors);
        return false;
      }

      var selectedPopulations = toCleanArray($scope.populations);

      if ( $state.current.name == "project.edit" ) {
        var message;
        if ( !angular.equals(
                selectedPopulations,$scope.projectInfo.populations ) ) {
          $scope.editParams.canUpdate =
              selectedPopulations.length == $scope.projectInfo.populations.length;
          message = 'You have made changes to populations. All existing data will be lost. Would you like to continue?';
          if ($scope.editParams.canUpdate) {
            message = 'You have changed some population parameters. Your original data can be reapplied, but you will have to redo the calibration and analysis. Would you like to continue?';
          }
          modalService.confirm(
            function () { continueSubmitForm( selectedPopulations ); },
            function () {},
            'Yes, save this project',
            'No',
            message,
            'Save Project?'
          );
        } else {
          message = 'No parameters have been changed. Do you intend to reload the original data and start from scratch?';
          modalService.confirm(
            function () { continueSubmitForm( selectedPopulations ); },
            function () {},
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

    initialize();

  });

});
