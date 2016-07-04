define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('AnalysisOptimizationController', function (
      $scope, $http, $modal, toastr, modalService, activeProject, $timeout) {

    function initialize() {

      if (!activeProject.data.has_data) {
        modalService.inform(
          function () {
          },
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

      // Fetch list of program-set for open-project
      $http.get(
        '/api/project/' + $scope.state.activeProject.id + '/progsets')
      .success(function (response) {
        $scope.state.programSetList = response.progsets;

        // Fetch list of parameter-set for open-project
        $http.get(
          '/api/project/' + $scope.state.activeProject.id + '/parsets')
        .success(function (response) {
          $scope.state.parsets = response.parsets;

          // get optimizations
          $http.get(
            '/api/project/' + $scope.state.activeProject.id + '/optimizations')
          .success(function (response) {

            console.log('loading optimizations', JSON.stringify(response, null, 2));
            $scope.state.optimizations = response.optimizations;
            convert_to_percentages($scope.state.optimizations);
            $scope.defaultOptimizationsByProgsetId = response.defaultOptimizationsByProgsetId;

            if ($scope.state.optimizations.length > 0) {
              $scope.setActiveOptimization($scope.state.optimizations[0]);
            } else {
              addNewOptimization('Optimization 1');
            }

            selectDefaultProgsetAndParset($scope.state.activeOptimization);
          });
        });
      });
    }

    function selectDefaultProgsetAndParset(optimization) {
      if (_.isUndefined(optimization.progset_id)) {
        if ($scope.state.programSetList.length > 0) {
          optimization.progset_id = $scope.state.programSetList[0].id;
        }
      }

      if (_.isUndefined(optimization.parset_id)) {
        if ($scope.state.parsets.length > 0) {
          optimization.parset_id = $scope.state.parsets[0].id;
        }
      }
    }

    $scope.setType = function (which) {
      $scope.state.activeOptimization.which = which;
      $scope.state.activeOptimization.objectives = objectiveDefaults[which];
      $scope.state.objectives = objectives[which];
    };

    var addNewOptimization = function (name) {
      console.log("Create new optimization");
      var newOptimization = {
        name: name,
        which: 'outcomes',
        constraints: {},
        objectives: {},
      };
      selectDefaultProgsetAndParset(newOptimization);
      $scope.state.optimizations.push(newOptimization);
      var progset_id = newOptimization.progset_id;
      var defaultOptimization = $scope.defaultOptimizationsByProgsetId[progset_id];
      newOptimization.constraints = defaultOptimization.constraints;
      newOptimization.objectives = defaultOptimization.objectives.outcomes;
      $scope.setActiveOptimization(newOptimization);
    };

    $scope.addOptimization = function() {
      openOptimizationModal(addNewOptimization, 'Add optimization', $scope.state.optimizations, null, 'Add');
    };

    function convert_to_percentages(optimizations) {
      _.each(optimizations, function(optimization) {
        _.each(["max", "min", "name"], function(prop) {
          var constraintList = optimization.constraints[prop];
          _.each(constraintList, function(val, key, list) {
            if (_.isNumber(val)) {
              list[key] = val * 100.0;
            }
          });
        });
      });
    };

    function convert_to_fractions(optimizations) {
      _.each(optimizations, function(optimization) {
        _.each(["max", "min", "name"], function(prop) {
          var constraintList = optimization.constraints[prop];
          _.each(constraintList, function(val, key, list) {
            if (_.isNumber(val)) {
              list[key] = val / 100.0;
            }
          });
        });
      });
    }

    $scope.setActiveOptimization = function(optimization) {
      $scope.state.activeOptimization = optimization;
      $scope.state.constraintKeys = _.keys(optimization.constraints.name);
      $scope.state.objectives = objectives[optimization.which];
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      console.log('active optim', $scope.state.activeOptimization);
      $scope.getOptimizationGraphs();
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
          $scope.setActiveOptimization(copyOptimization);
          $scope.state.optimizations.push($scope.state.activeOptimization);
        };
        openOptimizationModal(rename, 'Copy optimization', $scope.optimizations, $scope.state.activeOptimization.name + ' copy', 'Copy');
      }
    };

    function saveOptimizations() {
      var optimizations = angular.copy($scope.state.optimizations)
      convert_to_fractions(optimizations);
      console.log('saving', optimizations);
      $http.post(
        '/api/project/' + $scope.state.activeProject.id + '/optimizations',
        optimizations)
      .success(function (response) {
        toastr.success('Saved optimization');
        $scope.state.optimizations = response.optimizations;
        convert_to_percentages($scope.state.optimizations);
        console.log('returned saved optimizations', $scope.state.optimizations);
        if (!_.isUndefined($scope.state.activeOptimization)) {
          var name = $scope.state.activeOptimization.name;
          $scope.state.activeOptimization = _.findWhere($scope.state.optimizations, { 'name': name });
        }
      });
    }

    var removeActiveOptimization = function () {
      $scope.state.optimizations = _.filter($scope.state.optimizations, function (optimization) {
        return optimization.name !== $scope.state.activeOptimization.name;
      });
      if($scope.state.optimizations && $scope.state.optimizations.length > 0) {
        $scope.state.activeOptimization = $scope.state.optimizations[0];
      } else {
        $scope.state.activeOptimization = undefined;
      }
      saveOptimizations();
    };

    // Delete optimization
    $scope.deleteOptimization = function() {
      if (!$scope.state.activeOptimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        modalService.confirm(
          function () { removeActiveOptimization() },
          _.noop,
          'Yes, remove this optimization',
          'No',
          'Are you sure you want to permanently remove optimization "' + $scope.state.activeOptimization.name + '"?',
          'Delete optimization'
        );
      }
    };

    $scope.saveOptimizationForm = function(optimizationForm) {
      $scope.validateOptimizationForm(optimizationForm);
      if(!optimizationForm.$invalid) {
        saveOptimizations();
      }
    };

    $scope.validateOptimizationForm = function(optimizationForm) {
      optimizationForm.progset.$setValidity("required", !(!$scope.state.activeOptimization || !$scope.state.activeOptimization.progset_id));
      optimizationForm.parset.$setValidity("required", !(!$scope.state.activeOptimization || !$scope.state.activeOptimization.parset_id));
      optimizationForm.start.$setValidity("required", !(!$scope.state.activeOptimization || !$scope.state.activeOptimization.objectives.start));
      optimizationForm.end.$setValidity("required", !(!$scope.state.activeOptimization || !$scope.state.activeOptimization.objectives.end));
    };

    $scope.runOptimizations = function() {
      if($scope.state.activeOptimization.id) {
        $http.post(
          '/api/project/' + $scope.state.activeProject.id
          + '/optimizations/' + $scope.state.activeOptimization.id
          + '/results')
        .success(function (response) {
          if (response.status === 'started') {
            $scope.statusMessage = 'Optimization started.';
            $scope.errorMessage = '';
            $scope.seconds = 0;
            pollOptimizations();
          } else if (response.status === 'running') {
            $scope.statusMessage = 'Optimization already running.'
          }
        });
      }
    };

    var pollOptimizations = function() {
      $http.get(
        '/api/project/' + $scope.state.activeProject.id
        + '/optimizations/' + $scope.state.activeOptimization.id
        + '/results')
      .success(function(response) {
        if(response.status === 'completed') {
          $scope.getOptimizationGraphs();
          $scope.statusMessage = 'Optimization successfully completed updating graphs.';
          $timeout.cancel($scope.pollTimer);
        } else if(response.status === 'started'){
          $scope.pollTimer = $timeout(pollOptimizations, 2000);
          $scope.seconds += 2;
          $scope.statusMessage = "Optimization running for " + $scope.seconds + "s"
        }
      })
      .error(function() {
        $scope.errorMessage = 'Optimization failed.';
        $scope.statusMessage = '';
      });
    };

    var clearStatusMessage = function() {
      $timeout(function() {
        $scope.statusMessage = '';
      }, 5000);
    };

    $scope.getOptimizationGraphs = function() {
      var data = {};
      if($scope.state.activeOptimization.id) {
        if ($scope.selectors) {
          var selectors = _.filter($scope.selectors, function (selector) {
            return selector.checked;
          }).map(function (selector) {
            return selector.key;
          });
          if (selectors && selectors.length > 0) {
            data.which = selectors;
          }
        }
        $http.get(
          '/api/project/' + $scope.state.activeProject.id
          + '/optimizations/' + $scope.state.activeOptimization.id
          + '/graph',
          {params: data})
        .success(function (response) {
          clearStatusMessage();
          $scope.graphs = response.graphs;
        })
        .error(function() {
          clearStatusMessage();
        });
      }
    };

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

    initialize();

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
  outcomes: [
    { key: 'start', label: 'Year to begin optimization' },
    { key: 'end', label: 'Year by which to achieve objectives' },
    { key: 'budget', label: 'Starting budget' },
    { key: 'deathweight', label: 'Relative weight per death' },
    { key: 'inciweight', label: 'Relative weight per new infection' }
  ],
  money: [
    {key: 'base', label: 'Baseline year to compare outcomes to' },
    { key: 'start', label: 'Year to begin optimization' },
    { key: 'end', label: 'Year by which to achieve objectives' },
    { key: 'budget', label: 'Starting budget' },
    { key: 'deathfrac', label: 'Fraction of deaths to be averted' },
    { key: 'incifrac', label: 'Fraction of infections to be averted' }
  ]
};

var objectiveDefaults = {
  outcomes: {
    base: undefined,
    start: 2017,
    end: 2030,
    budget: 63500000.0,
    deathweight: 0,
    inciweight: 0
  },
  money: {
    base: 2015,
    start: 2017,
    end: 2030,
    budget: 63500000.0,
    deathfrac: 0,
    incifrac: 0
  }
};
