define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';


  module.factory('globalOptimizationPoller', ['$http', '$timeout', function($http, $timeout) {

    var optimPolls = {}

    function getOptimPoll(optimId) {
      if (!(optimId in optimPolls)) {
        console.log('Creating polling slot for', optimId)
        optimPolls[optimId] = {isRunning: false}
      }
      return optimPolls[optimId];
    }

    function start(optimName, projectId, optimId, callback) {
      var optimPoll = getOptimPoll(optimId);
      optimPoll.optimId = optimId;
      optimPoll.projectId = projectId;
      optimPoll.callback = callback;
      optimPoll.name = optimName;

      if (!optimPoll.isRunning) {

        console.log('Launch polling for', optimName, optimId);
        optimPoll.isRunning = true;

        function poller() {
          var optimPoll = getOptimPoll(optimId);
          $http.get(
            '/api/project/' + optimPoll.projectId
            + '/optimizations/' + optimPoll.optimId
            + '/results')
          .success(function(response) {
            if (response.status === 'started') {
              optimPoll.timer = $timeout(poller, 1000);
            } else {
              end(optimId);
            }
            optimPoll.callback(optimId, response);
          })
          .error(function() {
            end(optimId);
            optimPoll.callback(optimId, response);
          });
        }
        poller();

      } else {
        console.log('Taking over polling', optimName, optimId);
      }

    }

    function end(optimId) {
      var optimPoll = getOptimPoll(optimId);
      console.log('Stopping polling for', optimId, optimPoll);
      if (optimPoll.isRunning) {
        optimPoll.isRunning = false;
        $timeout.cancel(optimPoll.timer);
      }
    }

    return {
      start: start,
      end: end
    };

  }]);



  module.controller('AnalysisOptimizationController', function (
      $scope, $http, $modal, toastr, modalService, activeProject, $timeout, globalOptimizationPoller) {

    function initialize() {

      $scope.isPolling = {};

      if (!activeProject.data.hasData) {
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
        maxtime: 10,
        isRunnable: false,
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

            console.log('loading optimizations', response);
            $scope.state.optimizations = response.optimizations;
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

    $scope.checkNotSavable = function() {
      return !$scope.state.activeOptimization;
    };

    $scope.checkNotRunnable = function() {
      return !$scope.state.activeOptimization || !$scope.state.activeOptimization.id || !$scope.state.isRunnable;
    };

    $scope.setActiveOptimization = function(optimization) {
      if ($scope.state.activeOptimization) {
        globalOptimizationPoller.end($scope.state.activeOptimization.id);
      }

      $scope.state.isRunnable = false;
      $scope.state.activeOptimization = optimization;
      $scope.state.constraintKeys = _.keys(optimization.constraints.name);
      $scope.state.objectives = objectives[optimization.which];

      // clear screen
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      $scope.graphs = {};
      $scope.statusMessage = '';

      $http.get(
        '/api/project/' + $scope.state.activeProject.id
          + '/optimizations/' + $scope.state.activeOptimization.id
          + '/results')
      .success(function (response) {
        if (response.status === 'started') {
          initPollOptimizations();
        } else {
          $scope.getOptimizationGraphs();
        }
      });
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
      console.log('saving', $scope.state.optimizations);
      $http.post(
        '/api/project/' + $scope.state.activeProject.id + '/optimizations',
        $scope.state.optimizations)
      .success(function (response) {
        toastr.success('Saved optimization');
        $scope.state.optimizations = response.optimizations;
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

    $scope.startOptimization = function() {
      if($scope.state.activeOptimization.id) {
        $scope.state.isRunnable = false;
        $http.post(
          '/api/project/' + $scope.state.activeProject.id
            + '/optimizations/' + $scope.state.activeOptimization.id
            + '/results',
          { maxtime: $scope.state.maxtime })
        .success(function (response) {
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
      var optim = $scope.state.activeOptimization;
      globalOptimizationPoller.start(
          optim.name,
          $scope.state.activeProject.id,
          optim.id,
          pollCallback);
    }

    function pollCallback(optimId, response) {
      if (optimId != $scope.state.activeOptimization.id) {
        return;
      }
      if (response.status === 'completed') {
        $scope.statusMessage = '';
        toastr.success('Optimization completed');
        console.log('Get graphs of', $scope.state.activeOptimization.name)
        $scope.getOptimizationGraphs();
      } else if (response.status === 'error') {
        $scope.statusMessage = 'Optimization failed';
        $scope.errorMessage = response.error_text;
        $scope.state.isRunnable = true;
      } else if (response.status === 'started') {
        var start = new Date(response.start_time);
        var now = new Date();
        var diff = now.getTime() - start.getTime();
        var seconds = parseInt(diff / 1000);
        $scope.statusMessage = "Optimization running for " + seconds + " s";
      } else {
        $scope.errorMessage = response.error_text;
        $scope.statusMessage = 'Error polling optimization.';
        $scope.state.isRunnable = true;
      }
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
      if (!$scope.state.activeOptimization.id) {
        return;
      }
      var which = getSelectors();
      $http.post(
          '/api/project/' + $scope.state.activeProject.id
          + '/optimizations/' + $scope.state.activeOptimization.id
          + '/graph',
        {which: which})
      .success(function (response) {
        if (response.graphs) {
          toastr.success('Graphs loaded');
          $scope.graphs = response.graphs;
        }
        $scope.state.isRunnable = true;
      })
      .error(function(response) {
        $scope.state.isRunnable = true;
        toastr.error('response');
      });
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
