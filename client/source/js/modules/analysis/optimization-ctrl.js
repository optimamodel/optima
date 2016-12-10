define(
  ['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisOptimizationController', function (
      $scope, $http, $upload, $modal, toastr, modalService,
      activeProject, $timeout, globalPoller) {

    function initialize() {

      $scope.isMissingData = !activeProject.data.hasParset;
      $scope.isOptimizable = activeProject.data.isOptimizable;
      $scope.isMissingProgset = activeProject.data.nProgram == 0;

      $scope.editOptimization = openOptimizationModal;
      $scope.getParsetName = getParsetName;
      $scope.getProgsetName = getProgsetName;

      $scope.state = {
        project: activeProject.data,
        maxtime: 10,
        isRunnable: false,
        optimizations: []
      };

      if ($scope.isMissingData || $scope.isMissingProgset || !$scope.isOptimizable) {
        return
      }

      $http
        .get('/api/project/' + $scope.state.project.id + '/progsets')
        .then(function (response) {
          $scope.state.progsets = response.data.progsets;
          return $http.get('/api/project/' + $scope.state.project.id + '/parsets');
        })
        .then(function (response) {
          $scope.state.parsets = response.data.parsets;
          return $http.get('/api/project/' + $scope.state.project.id + '/optimizations')
        })
        .then(function (response) {
          var data = response.data;
          $scope.state.optimizations = data.optimizations;
          console.log('optimizations', data.optimizations);
          $scope.defaultOptimizationsByProgsetId = data.defaultOptimizationsByProgsetId;
          console.log('defaultOptimizationsByProgsetId', $scope.defaultOptimizationsByProgsetId);
          $scope.state.optimization = undefined;
          if ($scope.state.optimizations.length > 0) {
            $scope.setActiveOptimization($scope.state.optimizations[0]);
            selectDefaultProgsetAndParset($scope.state.optimization);
          }
        });
    }

    function selectDefaultProgsetAndParset(optimization) {
      if (_.isUndefined(optimization.progset_id)) {
        if ($scope.state.progsets.length > 0) {
          optimization.progset_id = $scope.state.progsets[0].id;
        }
      }
      if (_.isUndefined(optimization.parset_id)) {
        if ($scope.state.parsets.length > 0) {
          optimization.parset_id = $scope.state.parsets[0].id;
        }
      }
    }

    function getParsetName(optimization) {
      var parset_id = optimization.parset_id;
      var parset = _.find($scope.state.parsets, function(parset) {
        return parset.id == parset_id;
      });
      return parset.name
    }

    function getProgsetName(optimization) {
      var parset_id = optimization.parset_id;
      var parset = _.find($scope.state.parsets, function(parset) {
        return parset.id == parset_id;
      });
      return parset.name
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
              getOptimizationGraphs();
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

    function deepCopyJson(jsonObject) {
      return JSON.parse(JSON.stringify(jsonObject));
    }

    $scope.copyOptimization = function(optimization) {
      function copy(name) {
        var copyOptimization = deepCopyJson(optimization);
        copyOptimization.name = name;
        delete copyOptimization.id;
        $scope.setActiveOptimization(copyOptimization);
        $scope.state.optimizations.push(copyOptimization);
        saveOptimizations();
      }
      var names = _.pluck($scope.state.optimizations, 'name');
      var name = $scope.state.optimization.name;
      copy(modalService.getUniqueName(name, names));
    };

    $scope.deleteOptimization = function(deleteOptimization) {
      modalService.confirm(
        function() {
          function isSelected(optimization) {
            return optimization.name !== deleteOptimization.name;
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
    };

    $scope.downloadOptimization = function(optimization) {
      var data = JSON.stringify(angular.copy(optimization), null, 2);
      var blob = new Blob([data], { type: 'application/octet-stream' });
      saveAs(blob, (optimization.name + '.optim.json'));
    };

    $scope.uploadOptimization = function(optimization) {
      angular
        .element('<input type=\'file\'>')
        .change(
          function(event) {
            $upload.upload({
              url: '/api/project/' + $scope.state.project.id
                    + '/optimization/' + optimization.id
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

    $scope.startOptimization = function(optimization) {
      $scope.state.isRunnable = false;
      $http
        .post(
          '/api/project/' + $scope.state.project.id
            + '/optimizations/' + optimization.id
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
            getOptimizationGraphs();
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

    function getOptimizationGraphs() {
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
    }

    function saveOptimization(saveOptim) {
      var isExisting = false;
      _.each($scope.state.optimizations, function(optim, i) {
        if (optim.id == saveOptim.id) {
          $scope.state.optimizations[i] = saveOptim;
          isExisting = true;
        }
      });
      if (!isExisting) {
        $scope.state.optimizations.push(saveOptim);
      }
      saveOptimizations();
    }

    function swapKeysOfDictOfDict(dictOfDict) {
      var result = {};
      _.each(_.keys(dictOfDict), function(outerKey) {
        _.each(_.keys(dictOfDict[outerKey]), function(innerKey) {
          if (!_.has(result, innerKey)) {
            result[innerKey] = {};
          }
          result[innerKey][outerKey] = dictOfDict[outerKey][innerKey];
        });
      });
      return result;
    }

    function convertToKeyList(dict) {
      var result = [];
      _.mapObject(dict, function(value, key) {
        result.push(_.extend(deepCopyJson(value), {'key':key}));
      });
      return result;
    }

    function convertToDict(keyList) {
      var result = {};
      _.each(keyList, function(entry) {
        var newEntry = deepCopyJson(entry);
        var key = newEntry.key;
        result[key] = _.omit(newEntry, 'key');
      });
      return result;
    }

    function listifyConstraints(constraints) {
      return convertToKeyList(swapKeysOfDictOfDict(constraints));
    }

    function revertToConstraints(listOfConstraints) {
      var result = convertToDict(listOfConstraints);
      var result2 = swapKeysOfDictOfDict(result);
      return result2;
    }

    var optimVm = $scope;

    function openOptimizationModal(optimization) {

      function OptimizationModalController($scope, $modalInstance) {

        function initialize() {
          $scope.state = {};
          $scope.state.optimization = angular.copy(optimization);
          $scope.state.optimization.constraints = listifyConstraints(
            $scope.state.optimization.constraints);
          console.log("list of constraints", $scope.state.optimization.constraints);
          $scope.state.programShorts = _.keys($scope.state.optimization.constraints.name);
          $scope.parsets = optimVm.state.parsets;
          $scope.otherNames = _.without(_.pluck(optimVm.state.optimizations, 'name'), optimization.name);
          $scope.progsets = optimVm.state.progsets;
          $scope.cancel = cancel;
          $scope.save = save;
          $scope.isNameClash = isNameClash;
          $scope.addProgram = addProgram;
          $scope.selectProgset = selectProgset;

          $scope.defaultOptimizationsByProgsetId = optimVm.defaultOptimizationsByProgsetId;
          var progsetId = $scope.state.optimization.progset_id;
          $scope.defaultPrograms = listifyConstraints(
            deepCopyJson(optimVm.defaultOptimizationsByProgsetId[progsetId].constraints));
          console.log("list of default constraints", $scope.defaultPrograms);
        }

        function selectProgset() {
        }

        function addProgram() {
          $scope.state.optimization.constraints.push(
            deepCopyJson($scope.defaultPrograms[0]));
        }

        function changeConstraint(i) {
          console.log('change Constraint', i, $scope.state.optimization.constraints[i]);
        }

        function cancel() { $modalInstance.dismiss("cancel"); }

        function save() {
          console.log('saving from modal', $scope.state.optimization.constraints);
          $scope.state.optimization.constraints = revertToConstraints(
            $scope.state.optimization.constraints);
          console.log('converted constraints', $scope.state.optimization.constraints);
          $modalInstance.close($scope.state.optimization);
        }

        function isNameClash(name) {
          return _.contains($scope.otherNames, name);
        }

        initialize();

      }

      $modal
        .open({
          templateUrl: 'js/modules/analysis/optimization-modal.html',
          controller: OptimizationModalController,
          windowClass: 'fat-modal',
        })
        .result
        .then(function(optimization) {
          console.log('save optimization', optimization);
          saveOptimization(optimization);
          $scope.state.optimization = optimization;
        });
    }

    $scope.addOptimization = function(which) {
      var newOptimization = {
        name: name,
        which: which,
        constraints: {},
        objectives: {}
      };
      selectDefaultProgsetAndParset(newOptimization);
      $scope.state.optimizations.push(newOptimization);
      var progset_id = newOptimization.progset_id;
      var defaultOptimization = $scope.defaultOptimizationsByProgsetId[progset_id];
      newOptimization.constraints = [];
      newOptimization.objectives = defaultOptimization.objectives[which];
      openOptimizationModal(newOptimization);
    };

    initialize();

  });
});


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
