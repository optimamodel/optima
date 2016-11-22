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

      $scope.submitButtonText = "Create project & Download template data spreadsheet";
      $scope.populations = populations.data.populations;
      console.log('default populations', $scope.populations);

      if (isEditMode()) {
        $scope.submitButtonText = "Save project & Optima template";
        $scope.editParams.isEdit = true;

        if (activeProject.isSet()) {
          $scope.projectParams.id = $scope.projectInfo.id;
          $scope.projectParams.name = $scope.projectInfo.name;
          $scope.projectParams.startYear = $scope.projectInfo.startYear;
          $scope.projectParams.endYear = $scope.projectInfo.endYear;
        }

        var newPopulations = _($scope.projectInfo.populations).filter(isNotInScopePopulations);
        $scope.populations = $scope.populations.concat(newPopulations);

        // replace population attrs in $scope.populations
        // by $scope.projectInfo.populations
        _($scope.populations).each(function(population) {
          var source = findByShortAndName($scope.projectInfo.populations, population);
          if (source) {
            population.active = true;
            _.extend(population, source);
          }
        });
      }
    }

    function isNotInScopePopulations(testPopulation) {
      function sameAsTestPopulation(population) {
        return testPopulation.name === population.name
            && testPopulation.short === population.short;
      }
      return !_.find($scope.populations, sameAsTestPopulation);
    }

    function isEditMode(){
      return $state.current.name == "project.edit";
    }

    function findByShortAndName(arr, obj){
        return _.findWhere(arr, {short: obj.short, name: obj.name});
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
      if ($scope.projectParams.startYear) {
        var startYear = parseInt($scope.projectParams.startYear)
        return startYear < 1900 || 2100 < startYear;
      }
      return !$scope.projectParams.startYear;
    };

    $scope.invalidDataEnd = function() {
      if ($scope.projectParams.endYear) {
        var endYear = parseInt($scope.projectParams.endYear)
        if (endYear < 1900 || 2100 < endYear) {
          return true;
        }
        if ($scope.invalidDataStart()) {
          return false;
        }
        var startYear = parseInt($scope.projectParams.startYear)
        return endYear <= startYear;
      }
      return !$scope.projectParams.endYear;
    };

    $scope.invalidPopulationSelected = function() {
      var result = _.find($scope.populations, function(population) {
        return population.active === true;
      });
      return !result;
    };

    $scope.invalid = function() {
      return $scope.invalidName() || $scope.invalidDataStart()
        || $scope.invalidDataEnd() || $scope.invalidPopulationSelected();
    };

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

    $scope.openAddPopulationModal = function ($event) {
      if ($event) {
        $event.preventDefault();
      }
      var population = {
        short: '',
        name: '',
        age_to: '',
        age_from: '',
        female: false,
        male: false,
      };

      return openPopulationModal(population).result.then(
        function (newPopulation) {
          $scope.populations.push(newPopulation);
        }
      );
    };

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

    function getSelectedPopulations() {
      var populations = $scope.populations;
      return _(populations).chain()
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

    function saveProject(isUpdate, isDeleteData, isSpreadsheet) {
      console.log('isUpdate', isUpdate, 'isDeleteData', isDeleteData, 'isSpreadsheet', isSpreadsheet)
      var params = angular.copy($scope.projectParams);
      params.populations = getSelectedPopulations();
      var promise;
      var responseType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      if (isUpdate) {
        promise = projectApiService.updateProject(
          $scope.projectInfo.id,
          {
            project: params,
            isSpreadsheet: isSpreadsheet,
            isDeleteData: true,
          });
      } else {
        promise = projectApiService.createProject(params);
      }
      promise
        .success(function (response, status, headers) {
          if (responseType) {
            var blob = new Blob([response], {type: responseType});
            saveAs(blob, ($scope.projectParams.name + '.xlsx'));
            var newProjectId = headers()['x-project-id'];
            activeProject.setActiveProjectFor(
                $scope.projectParams.name, newProjectId, UserManager.data);
          }
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

      function removeExtraFields(aDict) {
        var copyDict = angular.copy(aDict);
        if (copyDict.hasOwnProperty("$$hashKey")) {
          delete copyDict["$$hashKey"];
        }
        if (copyDict.hasOwnProperty("active")) {
          delete copyDict["active"];
        }
        return copyDict;
      }

      if ($state.current.name == "project.edit") {
        var selectedPopulations = _.map(getSelectedPopulations(), removeExtraFields);
        var originalPopulations = _.map($scope.projectInfo.populations, removeExtraFields);
        var isPopulationsSame = angular.equals(selectedPopulations, originalPopulations);
        if (isPopulationsSame) {
          saveProject(true, false, true)
        } else {
          modalService.confirm(
              function() { saveProject(true, true, true) },
              function() {},
              'Yes, save this project',
              'No',
              'You have made changes to populations. All existing data will be lost. Would you like to continue?',
              'Save Project?'
          );
        }
      } else {
        // Create new project
        saveProject(false, false, true);
      }
    };

    initialize();

  });

});
