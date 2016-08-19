define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';


  module.factory('globalOptimizationPoller', ['$http', '$timeout', function($http, $timeout) {

    var optimPolls = {};

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
          $http
            .get(
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
            .error(function(response) {
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
      $scope, $http, $upload, $modal, toastr, modalService, activeProject, $timeout, globalOptimizationPoller) {

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

                  // fill in missing program constraints from default
                  _.each($scope.state.optimizations, function(optimization) {
                    var progset_id = optimization.progset_id;
                    var defaultOptimization = $scope.defaultOptimizationsByProgsetId[progset_id];
                    var keys = _.keys(defaultOptimization.constraints.name);
                    _.each(keys, function(key) {
                      console.log('check ', optimization.name, key, _.has(optimization.constraints, key));
                      if (!_.has(optimization.constraints.name, key)) {
                        optimization.constraints.max[key] = defaultOptimization.constraints.max[key];
                        optimization.constraints.min[key] = defaultOptimization.constraints.min[key];
                        optimization.constraints.name[key] = defaultOptimization.constraints.name[key];
                      };
                    });
                  });

                  if ($scope.state.optimizations.length > 0) {
                    $scope.setActiveOptimization($scope.state.optimizations[0]);
                  } else {
                    addNewOptimization('Optimization 1');
                  }

                  selectDefaultProgsetAndParset($scope.state.optimization);

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
      if ($scope.state.optimization) {
        globalOptimizationPoller.end($scope.state.optimization.id);
      }

      $scope.state.isRunnable = false;
      $scope.state.optimization = optimization;
      $scope.state.constraintKeys = _.keys(optimization.constraints.name);
      $scope.objectiveLabels = objectiveLabels[optimization.which];

      // clear screen
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      $scope.graphs = {};
      $scope.statusMessage = '';

      // not a new optimization
      if ($scope.state.optimization.id) {
        $http
          .get(
            '/api/project/' + $scope.state.project.id
              + '/optimizations/' + $scope.state.optimization.id
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
      console.log('returned saved optimizations', $scope.state.optimizations);
      if (name !== null) {
        $scope.state.optimization = _.findWhere(
            $scope.state.optimizations, { 'name': name });
      }
    }

    function saveOptimizations() {
      console.log('saving optimizations', $scope.state.optimizations);
      $http.post(
        '/api/project/' + $scope.state.project.id + '/optimizations',
        $scope.state.optimizations)
      .success(loadOptimizations);
    }

    var openOptimizationModal = function (
        callback, title, optimizationList, optimizationName, operation, isRename) {

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

    $scope.addOptimization = function() {
      openOptimizationModal(
        function (name) {
          console.log("Create new optimization");
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
        },
        'Add optimization',
        $scope.state.optimizations,
        null,
        'Add');
    };

    $scope.renameOptimization = function () {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        openOptimizationModal(
          function(name) {
            $scope.state.optimization.name = name;
            saveOptimizations();
          },
          'Rename optimization',
          $scope.state.optimizations,
          $scope.state.optimization.name,
          'Rename',
          true);
      }
    };

    $scope.copyOptimization = function() {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        openOptimizationModal(
          function (name) {
            var copyOptimization = angular.copy($scope.state.optimization);
            copyOptimization.name = name;
            delete copyOptimization.id;
            $scope.setActiveOptimization(copyOptimization);
            $scope.state.optimizations.push($scope.state.optimization);
            saveOptimizations();
          },
          'Copy optimization',
          $scope.state.optimizations,
          $scope.state.optimization.name + ' copy',
          'Copy');
      }
    };

    $scope.deleteOptimization = function() {
      if (!$scope.state.optimization) {
        modalService.informError([{message: 'No optimization selected.'}]);
      } else {
        modalService.confirm(
          function () {
            function isActive(optimization) {
              return optimization.name !== $scope.state.optimization.name;
            }
            $scope.state.optimizations = _.filter($scope.state.optimizations, isActive);
            if($scope.state.optimizations && $scope.state.optimizations.length > 0) {
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
      globalOptimizationPoller.start(
        $scope.state.optimization.name,
        $scope.state.project.id,
        $scope.state.optimization.id,
        pollCallback);
    }

    function pollCallback(optimId, response) {
      if (optimId != $scope.state.optimization.id) {
        return;
      }
      if (response.status === 'completed') {
        $scope.statusMessage = 'Loading graphs...';
        toastr.success('Optimization completed');
        $scope.getOptimizationGraphs();
      } else if (response.status === 'started') {
        var start = new Date(response.start_time);
        var now = new Date();
        var diff = now.getTime() - start.getTime();
        var seconds = parseInt(diff / 1000);
        $scope.statusMessage = "Optimization running for " + seconds + " s";
      } else {
        $scope.statusMessage = 'Optimization failed';
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
            $scope.graphs = response.graphs;
          }
          $scope.state.isRunnable = true;
          $scope.statusMessage = '';
        })
        .error(function(response) {
          $scope.state.isRunnable = true;
          toastr.error('response');
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
