define(
  ['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisOptimizationController', function (
      $scope, $http, $upload, $modal, toastr, modalService,
      activeProject, $timeout, globalPoller) {

    function initialize() {

      $scope.isPolling = {};

      $scope.isMissingData = !activeProject.data.hasParset;
      $scope.isOptimizable = activeProject.data.isOptimizable;
      $scope.isMissingProgramSet = activeProject.data.nProgram == 0;

      if ($scope.isMissingData || $scope.isMissingProgramSet || !$scope.isOptimizable) {
        return
      }

      $scope.state = {
        project: activeProject.data,
        maxtime: 10,
        isRunnable: false,
        optimizations: []
      };

      // Fetch list of program-set for open-project
      $http
        .get(
          '/api/project/' + $scope.state.project.id + '/progsets')
        .success(function (response) {
          $scope.state.programSetList = response.progsets;

          // Fetch list of parameter-set for open-project
          $http
            .get(
              '/api/project/' + $scope.state.project.id + '/parsets')
            .success(function (response) {
              $scope.state.parsets = response.parsets;

              // get optimizations
              $http
                .get(
                  '/api/project/' + $scope.state.project.id + '/optimizations')
                .success(function (response) {

                  console.log('loading optimizations', response);
                  $scope.state.optimizations = response.optimizations;

                  $scope.defaultOptimizationsByProgsetId = response.defaultOptimizationsByProgsetId;

                  if ($scope.state.optimizations.length > 0) {
                    $scope.setActiveOptimization($scope.state.optimizations[0]);
                    selectDefaultProgsetAndParset($scope.state.optimization);
                  } else {
                    $scope.state.optimization = undefined;
                  }

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
      $scope.state.optimization.which = which;
      $scope.state.optimization.objectives = objectiveDefaults[which];
      $scope.objectiveLabels = objectiveLabels[which];
    };

    $scope.checkNotSavable = function() {
      return !$scope.state.optimization;
    };

    $scope.checkNotRunnable = function() {
      return !$scope.state.optimization || !$scope.state.optimization.id || !$scope.state.isRunnable;
    };

    $scope.setActiveOptimization = function(optimization) {
      $scope.state.optimization = optimization;
      $scope.selectOptimization();
    };

    $scope.selectOptimization = function() {
      globalPoller.stopPolls();

      $scope.state.isRunnable = false;
      var optimization = $scope.state.optimization;
      $scope.state.constraintKeys = _.keys(optimization.constraints.name);
      $scope.objectiveLabels = objectiveLabels[optimization.which];

      // clear screen
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      $scope.graphs = {};
      $scope.statusMessage = '';

      // not a new optimization
      if (optimization.id) {
        $http
          .get(
            '/api/project/' + $scope.state.project.id
              + '/optimizations/' + optimization.id
              + '/results')
          .success(function(response) {
            if (response.status === 'started') {
              initPollOptimizations();
            } else {
              $scope.statusMessage = 'Checking for pre-calculated figures...';
              $scope.getOptimizationGraphs();
            }
          });
      } else {
        $scope.state.isRunnable = true;
      }
    };

    function loadOptimizations(response) {
      toastr.success('Saved optimization');
      var name = null;
      if (!_.isUndefined($scope.state.optimization)) {
        name = $scope.state.optimization.name;
      }
      $scope.state.optimizations = response.optimizations;
      if (name == null) {
        $scope.state.optimization = null;
      } else {
        $scope.state.optimization = _.findWhere(
          $scope.state.optimizations, {'name': name});
      }
      console.log('loaded optimizations', $scope.state.optimizations);
      console.log('selected optimization', name, $scope.state.optimization);
    }

    function saveOptimizations() {
      console.log('saving optimizations', $scope.state.optimizations);
      $http.post(
        '/api/project/' + $scope.state.project.id + '/optimizations',
        $scope.state.optimizations)
      .success(loadOptimizations);
    }

    $scope.addOptimization = function() {

      function addNewOptimization(name) {
        var newOptimization = {
          name: name,
          which: 'outcomes',
          constraints: {},
          objectives: {}
        };
        selectDefaultProgsetAndParset(newOptimization);
        $scope.state.optimizations.push(newOptimization);
        var progset_id = newOptimization.progset_id;
        var defaultOptimization = $scope.defaultOptimizationsByProgsetId[progset_id];
        newOptimization.constraints = defaultOptimization.constraints;
        newOptimization.objectives = defaultOptimization.objectives.outcomes;
        $scope.setActiveOptimization(newOptimization);
        saveOptimizations();
      }

      modalService.rename(
        addNewOptimization,
        'Add optimization',
        'Enter name', '',
        'Name already exists',
        _.pluck($scope.state.optimizations, 'name'));
    };

    $scope.renameOptimization = function () {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        function rename(name) {
          $scope.state.optimization.name = name;
          saveOptimizations();
        }
        var name = $scope.state.optimization.name;
        var otherNames = _.pluck($scope.state.optimizations, 'name');
        modalService.rename(
          rename,
          'Rename parameter set',
          'Enter name',
          name,
          'Name already exists',
          _.without(otherNames, name)
        );
      }
    };

    function deepCopyJson(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
    }

    $scope.copyOptimization = function() {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        function copy(name) {
          var copyOptimization = deepCopyJson($scope.state.optimization);
          copyOptimization.name = name;
          delete copyOptimization.id;
          $scope.setActiveOptimization(copyOptimization);
          $scope.state.optimizations.push($scope.state.optimization);
          saveOptimizations();
        }
        var names = _.pluck($scope.state.optimizations, 'name');
        var name = $scope.state.optimization.name;
        modalService.rename(
          copy,
          'Copy optimization',
          'Copy',
          modalService.getUniqueName(name, names),
          'Name already exists',
          names);
      }
    };

    $scope.deleteOptimization = function() {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        modalService.confirm(
          function () {
            function isSelected(optimization) {
              return optimization.name !== $scope.state.optimization.name;
            }
            $scope.state.optimizations = _.filter($scope.state.optimizations, isSelected);
            if ($scope.state.optimizations && $scope.state.optimizations.length > 0) {
              $scope.state.optimization = $scope.state.optimizations[0];
            } else {
              $scope.state.optimization = undefined;
            }
            saveOptimizations();
          },
          _.noop,
          'Yes, remove this optimization',
          'No',
          'Are you sure you want to permanently remove optimization "' + $scope.state.optimization.name + '"?',
          'Delete optimization'
        );
      }
    };

    $scope.downloadOptimization = function() {
      var data = JSON.stringify(angular.copy($scope.state.optimization), null, 2);
      var blob = new Blob([data], { type: 'application/octet-stream' });
      saveAs(blob, ($scope.state.optimization.name + '.optim.json'));
    };

    $scope.uploadOptimization = function() {
      angular
        .element('<input type=\'file\'>')
        .change(
          function(event) {
            $upload.upload({
              url: '/api/project/' + $scope.state.project.id
                    + '/optimization/' + $scope.state.optimization.id
                    + '/upload',
              file: event.target.files[0]
            }).success(function(response) {
              loadOptimizations(response);
            });
          })
        .click();
    };

    $scope.saveOptimizationForm = function(optimizationForm) {
      $scope.validateOptimizationForm(optimizationForm);
      if(!optimizationForm.$invalid) {
        saveOptimizations();
      }
    };

    $scope.validateOptimizationForm = function(optimizationForm) {
      optimizationForm.progset.$setValidity(
          "required",
          !(!$scope.state.optimization || !$scope.state.optimization.progset_id));
      optimizationForm.parset.$setValidity(
          "required",
          !(!$scope.state.optimization || !$scope.state.optimization.parset_id));
      optimizationForm.start.$setValidity(
          "required",
          !(!$scope.state.optimization || !$scope.state.optimization.objectives.start));
      optimizationForm.end.$setValidity(
          "required",
          !(!$scope.state.optimization || !$scope.state.optimization.objectives.end));
    };

    $scope.startOptimization = function() {
      if($scope.state.optimization.id) {
        $scope.state.isRunnable = false;
        $http
          .post(
            '/api/project/' + $scope.state.project.id
              + '/optimizations/' + $scope.state.optimization.id
              + '/results',
            { maxtime: $scope.state.maxtime })
          .success(function (response) {
            $scope.task_id = response.task_id;
            if (response.status === 'started') {
              $scope.statusMessage = 'Optimization started.';
              initPollOptimizations();
            } else if (response.status === 'blocked') {
              $scope.statusMessage = 'Another calculation on this project is already running.'
            }
          });
      }
    };

    function initPollOptimizations() {
      globalPoller.startPoll(
        $scope.state.optimization.id,
        '/api/project/' + $scope.state.project.id
          + '/optimizations/' + $scope.state.optimization.id
          + '/results',
        function(response) {
          if (response.status === 'completed') {
            $scope.statusMessage = 'Loading graphs...';
            toastr.success('Optimization completed');
            $scope.getOptimizationGraphs();
          } else if (response.status === 'started') {
            $scope.task_id = response.task_id;
            var start = new Date(response.start_time);
            var now = new Date(response.current_time);
            var diff = now.getTime() - start.getTime();
            var seconds = parseInt(diff / 1000);
            $scope.statusMessage = "Optimization running for " + seconds + " s";
          } else {
            $scope.statusMessage = 'Optimization failed';
            $scope.state.isRunnable = true;
          }
        }
      );
    }

    function getSelectors() {
      if ($scope.graphs) {
        var selectors = $scope.graphs.selectors;
        if (selectors) {
          var which = _.filter(selectors, function(selector) {
            return selector.checked;
          })
          .map(function(selector) {
            return selector.key;
          });
          if (which.length > 0) {
            return which;
          }
        }
      }
      return null;
    }

    $scope.getOptimizationGraphs = function() {
      if (!$scope.state.optimization.id) {
        return;
      }
      $http
        .post(
          '/api/project/' + $scope.state.project.id
            + '/optimizations/' + $scope.state.optimization.id
            + '/graph',
          {which: getSelectors()})
        .success(function (response) {
          if (response.graphs) {
            toastr.success('Graphs loaded');
            console.log('graphs', response.graphs);
            $scope.graphs = response.graphs;
          }
          $scope.state.isRunnable = true;
          $scope.statusMessage = '';
        })
        .error(function(response) {
          $scope.state.isRunnable = true;
          toastr.error(response);
        });
    };

    initialize();

  });
});

// this is to be replaced by an api
var objectiveLabels = {
  outcomes: [
    { key: 'start', label: 'Year to begin optimization' },
    { key: 'end', label: 'Year by which to achieve objectives' },
    { key: 'budget', label: 'Starting budget' },
    { key: 'deathweight', label: 'Relative weight per death' },
    { key: 'inciweight', label: 'Relative weight per new infection' }
  ],
  money: [
    { key: 'base', label: 'Baseline year to compare outcomes to' },
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
