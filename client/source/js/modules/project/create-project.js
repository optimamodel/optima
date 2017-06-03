define(['angular', 'ui.router', './population-modal'], function (angular) {


  'use strict';


  var module = angular.module(
    'app.create-project', ['ui.router', 'app.population-modal']);


  module.config(function($stateProvider) {
    $stateProvider
      .state('createproject', {
        url: '/create-project',
        templateUrl: 'js/modules/project/create-project.html?cacheBust=xxx',
        controller: 'ProjectCreateOrEditController'
      });
  });


  module.controller('ProjectCreateOrEditController', function (
      $scope, $state, $modal, $timeout, userManager, modalService, projectService) {

    function initialize() {
      $scope.projects = projectService.projects;
      $scope.project = {name: ''};

      $scope.submitButtonText = "Create project & download data entry spreadsheet";
      projectService
        .getPopulations()
        .then(function(response) {
          $scope.populations = response.data.populations;
          console.log('initialize populations', $scope.populations);
        });
    }

    $scope.projectExists = function () {
      return _.some($scope.projects, function (project) {
        return $scope.project.name === project.name && $scope.project.id !== project.id;
      });
    };

    $scope.invalidName = function() {
      return !$scope.project.name;
    };

    $scope.invalidDataStart = function() {
      if ($scope.project.startYear) {
        var startYear = parseInt($scope.project.startYear)
        return startYear < 1900 || 2100 < startYear;
      }
      return !$scope.project.startYear;
    };

    $scope.invalidDataEnd = function() {
      if ($scope.project.endYear) {
        var endYear = parseInt($scope.project.endYear)
        if (endYear < 1900 || 2100 < endYear) {
          return true;
        }
        if ($scope.invalidDataStart()) {
          return false;
        }
        var startYear = parseInt($scope.project.startYear)
        return endYear <= startYear;
      }
      return !$scope.project.endYear;
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
        templateUrl: 'js/modules/project/population-modal.html?cacheBust=xxx',
        controller: 'ProjectCreatePopulationModalController',
        resolve: {
          populations: function(){ return $scope.populations; },
          population: function(){ return population; }
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

    function createProject(isUpdate, isDeleteData, isSpreadsheet) {
      var project = angular.copy($scope.project);
      project.populations = getSelectedPopulations();
      projectService
        .createProject(project)
        .then(function() {
          $state.go('home');
        });
    }

    $scope.submit = function () {
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

      createProject(false, false, true);
    };

    initialize();

  });

  return module;

});
