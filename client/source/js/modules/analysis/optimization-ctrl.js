define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  /**
   * Defines & validates objectives, parameters & constraints to run, display &
   * save optimization results.
   */
  module.controller('AnalysisOptimizationController', function ($scope, $http, $modal, modalService, activeProject, $timeout) {

    if (!activeProject.data.has_data) {
      modalService.inform(
        function (){ },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $scope.missingData = true;
      return;
    }

    $scope.state = {
      activeProject: activeProject.data,
      optimizations: []
    };

    $scope.setType = function(which) {
      $scope.state.activeOptimization.which = which;
      $scope.state.activeOptimization.objectives = objectiveDefaults[which];
      $scope.state.objectives = objectives[which];
    };

    $http.get('/api/project/' + $scope.state.activeProject.id + '/optimizations').
      success(function (response) {
        $scope.state.optimizations = response.optimizations;
        if($scope.state.optimizations.length > 0) {
          setActiveOptimization($scope.state.optimizations[0]);
        }
      });

    $scope.addOptimization = function() {
      var add = function (name) {
        var newOptimization = {
          name: name,
          which: 'money',
          constraints: constraints,
          objectives: objectiveDefaults.money
        };
        setActiveOptimization(newOptimization);
        $scope.state.optimizations.push(newOptimization);
      };
      openOptimizationModal(add, 'Add optimization', $scope.state.optimizations, null, 'Add');
    };

    var getConstraintKeys = function(constraints) {
      return _.keys(constraints.name);
    };

    var setActiveOptimization = function(optimization) {
      $scope.state.activeOptimization = optimization;
      $scope.state.constraintKeys = getConstraintKeys(optimization.constraints);
      $scope.state.objectives = objectives[optimization.which];
    };

    // Open pop-up to re-name Optimization
    $scope.renameOptimization = function () {
      if (!$scope.state.activeOptimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        var rename = function (name) {
          $scope.state.activeOptimization.name = name;
        };
        openOptimizationModal(rename, 'Rename optimization', $scope.state.optimizations, $scope.state.activeOptimization.name, 'Rename', true);
      }
    };

    // Copy Optimization
    $scope.copyOptimization = function() {
      if (!$scope.state.activeOptimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        var rename = function (name) {
          var copyOptimization = angular.copy($scope.state.activeOptimization);
          copyOptimization.name = name;
          setActiveOptimization(copyOptimization);
          $scope.state.optimizations.push($scope.state.activeOptimization);
        };
        openOptimizationModal(rename, 'Copy optimization', $scope.optimizations, $scope.state.activeOptimization.name + ' copy', 'Copy');
      }
    };

    // Delete optimization
    $scope.deleteOptimization = function() {
      if (!$scope.state.activeOptimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        var remove = function () {
          $scope.state.optimizations = _.filter($scope.state.optimizations, function (optimization) {
            return optimization.name !== $scope.state.activeOptimization.name;
          });
          if($scope.state.optimizations && $scope.state.optimizations.length > 0) {
            $scope.state.activeOptimization = $scope.state.optimizations[0];
          } else {
            $scope.state.activeOptimization = undefined;
          }
        };
        modalService.confirm(
          function () {
            remove()
          }, function () {
          }, 'Yes, remove this optimization', 'No',
          'Are you sure you want to permanently remove optimization "' + $scope.state.activeOptimization.name + '"?',
          'Delete optimization'
        );
      }
    };

    $scope.saveOptimization = function() {
      $http.post('/api/project/' + $scope.state.activeProject.id + '/optimizations', $scope.state.activeOptimization).
        success(function (response) {
          // setActiveOptimization(response);
        });
    };

    $scope.runOptimizations = function() {
      var data = {};
      $http.post('/api/project/' + $scope.state.activeProject.id + '/optimizations/' + $scope.state.activeOptimization.id + '/results')
        .success(function(response) {
          if(response.status === 'started') {
            $scope.statusMessage = 'Optimization started.';
            $scope.errorMessage = '';
              pollOptimizations();
          } else if(response.status === 'running') {
            $scope.statusMessage = 'Optimization already running.'
          }
        })
    };

    var pollOptimizations = function() {
      var that = this;
      $http.get('/api/project/' + $scope.state.activeProject.id + '/optimizations/' + $scope.state.activeOptimization.id + '/results')
        .success(function(response) {
          if(response.status === 'completed') {
            getOptimizationGraphs();
            $scope.statusMessage = 'Optimization successfully completed.';
            $timeout.cancel($scope.pollTimer);
          } else if(response.status === 'started'){
            $scope.pollTimer = $timeout(pollOptimizations, 5000);
          } else if(response.status === 'error'){
            $scope.errorMessage = 'Optimization failed.';
            $scope.statusMessage = '';
          }
        });
    };

    var getOptimizationGraphs = function() {
      $http.get('/api/project/' + $scope.state.activeProject.id + '/optimizations/' + $scope.state.activeOptimization.id + '/graph')
        .success(function(response) {
          console.log('graohs', response);
          $scope.optimizationCharts = response.optimization.graphs;
          $scope.selectors = response.optimization.selectors;
          $scope.statusMessage = 'Charts updated.';
        });
    };

    // Fetch list of program-set for open-project from BE
    $http.get('/api/project/' + $scope.state.activeProject.id + '/progsets').success(function (response) {
      $scope.state.programSetList = response.progsets;
    });

    // Fetch list of parameter-set for open-project from BE
    $http.get('/api/project/' + $scope.state.activeProject.id + '/parsets').success(function (response) {
      $scope.state.parsets = response.parsets;
    });

    // Opens modal to add / rename / copy optimization
    var openOptimizationModal = function (callback, title, optimizationList, optimizationName, operation, isRename) {
      var onModalKeyDown = function (event) {
        if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
      };
      var modalInstance = $modal.open({
        templateUrl: 'js/modules/analysis/optimization-modal.html',
        controller: ['$scope', '$document', function ($scope, $document) {
          $scope.title = title;
          $scope.name = optimizationName;
          $scope.operation = operation;
          $scope.updateOptimization = function () {
            $scope.newOptimizationName = $scope.name;
            callback($scope.name);
            modalInstance.close();
          };
          $scope.isUniqueName = function (optimizationForm) {
            var exists = _(optimizationList).some(function(item) {
                return item.name == $scope.name;
              }) && $scope.name !== optimizationName && $scope.name !== $scope.newOptimizationName;
            if(isRename) {
              optimizationForm.optimizationName.$setValidity("optimizationUpdated", $scope.name !== optimizationName);
            }
            optimizationForm.optimizationName.$setValidity("optimizationExists", !exists);
            return exists;
          };
          $document.on('keydown', onModalKeyDown); // observe
          $scope.$on('$destroy', function (){ $document.off('keydown', onModalKeyDown); });  // unobserve
        }]
      });
      return modalInstance;
    };

  });
});

//todo: add validations, comment code

// this is to be replaced by an api
var constraints = {
  'max': {'MSM programs': null, 'HTC mobile': null, 'ART': null, 'VMMC': null, 'HTC workplace': null, 'Condoms': null, 'PMTCT': null, 'Other': 1.0, 'MGMT': 1.0, 'HTC medical': null, 'FSW programs': null},
  'name': {'MSM programs': 'Programs for men who have sex with men', 'HTC mobile': 'HIV testing and counseling - mobile clinics', 'ART': 'Antiretroviral therapy', 'VMMC': 'Voluntary medical male circumcision', 'HTC workplace': 'HIV testing and counseling - workplace programs', 'Condoms': 'Condom promotion and distribution', 'PMTCT': 'Prevention of mother-to-child transmission', 'Other': 'Other', 'MGMT': 'Management', 'HTC medical': 'HIV testing and counseling - medical facilities', 'FSW programs': 'Programs for female sex workers and clients'},
  'min': {'MSM programs': 0.0, 'HTC mobile': 0.0, 'ART': 1.0, 'VMMC': 0.0, 'HTC workplace': 0.0, 'Condoms': 0.0, 'PMTCT': 0.0, 'Other': 1.0, 'MGMT': 1.0, 'HTC medical': 0.0, 'FSW programs': 0.0}
};

// this is to be replaced by an api
var objectives = {
  outcome: [
    { key: 'base', label: 'Baseline year to compare outcomes to' },
    { key: 'start', label: 'Year to begin optimization' },
    { key: 'end', label: 'Year by which to achiever objectives' },
    { key: 'budget', label: 'Starting budget' },
    { key: 'deathweight', label: 'Relative weight per death' },
    { key: 'inciweight', label: 'Relative weight per new infection' }
  ],
  money: [
    {key: 'base', label: 'Baseline year to compare outcomes to' },
    { key: 'start', label: 'Year to begin optimization' },
    { key: 'end', label: 'Year by which to achiever objectives' },
    { key: 'budget', label: 'Starting budget' },
    { key: 'deathfrac', label: 'Fraction of deaths to be averted' },
    { key: 'incifrac', label: 'Fraction of infections to be averted' }
  ]
};

var objectiveDefaults = {
  outcome: {
    base: undefined,
    start: 2017,
    end: 2013,
    budget: 63500000.0,
    deathweight: 0,
    inciweight: 0
  },
  money: {
    base: undefined,
    start: 2017,
    end: 2013,
    budget: 63500000.0,
    deathfrac: 0,
    incifrac: 0
  }
};
