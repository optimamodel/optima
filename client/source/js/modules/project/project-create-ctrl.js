define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectCreateController', function ($scope, $state, $modal,
    $timeout, activeProject, parametersResponse, defaultsResponse, project, UserManager, modalService) {

    $scope.projectParams = {
      name: ''
    };

    var availableParameters = parametersResponse.data.params;
    var availableDefaults = defaultsResponse.data;
    
    if ( $state.current.name == "project.edit" ) {
      
      // set project post mode to edit
      // $scope.is_edit = "true";
      document.getElementById('is_edit').value = "true";
      document.getElementById('old_project_name').value = project.name;

      if (activeProject.isSet()) {
        $scope.projectParams = project;

        $scope.projectParams.datastart = $scope.projectParams.dataStart;
        $scope.projectParams.dataend = $scope.projectParams.dataEnd;
        $scope.projectParams.econ_dataend = $scope.projectParams.projectionEndYear;
      }
      
      /**
       * Cannot use array.concat for following reasons
       * 1. The structure of both objects are different 
       * availableDefaults.populations has two additional properties $$hashKey and active,
       * that are missing in project.populations
       * 2. We need to mark objects in project.populations as active in availableDefaults.populations
       */
      // availableDefaults.populations = availableDefaults.populations.concat(project.populations);
      for ( var i in project.populations ) {
        var result = availableDefaults.populations.filter(function( obj ) {
          if ( obj.short_name == project.populations[i].short_name ) {
            // obj is a reference of objects in availableDefaults.populations
            obj.active = true;
            return true;
          }
        });

        if (result.length == 0) {
          project.populations[i].active = true;
          availableDefaults.populations.push( project.populations[i] );
        }
      }
      
      for ( var i in project.programs ) {
        var result = availableDefaults.programs.filter(function( obj ) {
          if ( obj.short_name == project.programs[i].short_name ) {
            // obj is a reference of objects in availableDefaults.populations
            obj.active = true;
            return true;
          }
        });

        if (result.length == 0) {
          project.programs[i].active = true;
          availableDefaults.programs.push( project.programs[i] );
        }
      }
        // change submit button name
        $scope.submit = "Save project & Optima template";
    } else {
        // change submit button name
        $scope.submit = "Create project & Optima template";
    }
    

    $scope.populations = availableDefaults.populations;
    $scope.programs = availableDefaults.programs;
    $scope.categories = availableDefaults.categories;

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
     * Filters programs by category
     */
    $scope.filterPrograms = function(category) {
      return _($scope.programs).filter(function (item) {
          return item.category==category.category;
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
    var openProgramModal = function (program) {
      return $modal.open({
        templateUrl: 'js/modules/project/create-program-modal.html',
        controller: 'ProjectCreateProgramModalController',
        resolve: {
          program: function () {
            return program;
          },
          availableParameters: function () {
            return availableParameters;
          },
          populations: function () {
            return $scope.populations;
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

    /*
     * Returns the provide programs with every "ALL_POPULATIONS" entry replaced
     * by the selected populations.
     *
     * Example: ['ALL_POPULATIONS'] -> ["FSW","CSW","MSM","PWID","CHILD","INF"]
     */
    var insertSelectedPopulations = function (programs, selectedPopulations) {
      var shortPopulationNames = _(selectedPopulations).pluck('short_name');
      return _(programs).map(function(program) {
        program.parameters = _(program.parameters).map(function(entry) {
          if (entry.value.pops[0] === "ALL_POPULATIONS") {
            entry.value.pops = shortPopulationNames;
          }
          return entry;
        });
        return program;
      });
    };

    $scope.prepareCreateForm = function () {

      if ($scope.CreateProjectForm.$invalid) {
        alert('Please fill in all the required project fields');
        return false;
      }

      var selectedPrograms = toCleanArray($scope.programs);
      var selectedPopulations = toCleanArray($scope.populations);
      
      if ( $state.current.name == "project.edit" ) {
        project.populations.forEach(function(obj){ 
          delete obj.active;
          delete obj.$$hashKey;
        });
        project.programs.forEach(function(obj){ 
          delete obj.active;
          delete obj.$$hashKey;
        });
        
        if ( !angular.equals( selectedPopulations,project.populations ) || !angular.equals( selectedPrograms,project.programs ) ) {
          var message = 'You have made changes in populations and/or programs, you are required to reupload data file';
          modalService.inform(
            function (){ null }, 
            'Okay',
            message, 
            'Alert!'
          );
        }
      }
      
      var params = _($scope.projectParams).omit('name');
      params.populations = selectedPopulations;
      params.programs = insertSelectedPopulations(selectedPrograms, selectedPopulations);

      $scope.formAction = '/api/project/create/' + $scope.projectParams.name;
      $scope.formParams = JSON.stringify(params);
      
      // according to documentation it should have been working without this line, but no cigar
      // https://docs.angularjs.org/api/ng/directive/ngSubmit
      document.getElementById('createForm').action = $scope.formAction;
      document.getElementById('params').value = $scope.formParams;
      document.getElementById('createForm').submit();

      // update active project
      activeProject.setActiveProjectFor($scope.projectParams.name, UserManager.data);

      // Hack to wait for the project to be created.
      // There is not easy way to intercept the completion of the form submission...
      $timeout(function () {
        $state.go('home');
      }, 3000);

      return true;
    };

  });

});
