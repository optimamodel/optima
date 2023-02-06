define(['angular', 'ui.router'], function (angular) {
  'use strict';

  
  var module = angular.module('app.optimization', ['ui.router',]);



  module.config(function ($stateProvider) {
    $stateProvider
      .state('optimization', {
        url: '/optimization',
        templateUrl: 'js/modules/optimization/optimization.html?cacheBust=xxx',
        controller: 'AnalysisOptimizationController'
      });
  });



  module.controller('AnalysisOptimizationController',
    function($scope, $modal, toastr, modalService, projectService, $timeout,
             pollerService, rpcService) {

      function initialize() {

      $scope.state = {
        project: undefined,
        maxtime: 10,
        isRunnable: false, // Decide whether to disable the button to launch task (disabled while loading task status)
        isRunning: false, // Decide whether or not to show cancel button (NOT shown while loading task status)
        graphs: undefined,
        optimizations: [],
        years: null,
        start: null,
        end: null,
        timer: null,
      };

      $scope.editOptimization = openEditOptimizationModal;
      $scope.getParsetName = getParsetName;
      $scope.getProgsetName = getProgsetName;

      $scope.anyOptimizable = false;

      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined($scope.state.project) && ($scope.state.project.id !== projectService.project.id)) {
          reloadActiveProject();
        }
      });

      $scope.$on('$destroy', function(){
        $timeout.cancel($scope.state.timer);
      });

      reloadActiveProject();
    }

    function reloadActiveProject() {
      projectService
        .getActiveProject()
        .then(function(response) {
          var project = response.data;
          $scope.state.project = project;
          $scope.state.years = _.range(project.startYear, project.endYear + 1);
          $scope.state.start = project.startYear;
          $scope.state.end = project.endYear;
          $scope.isMissingData = !project.calibrationOK;
          $scope.anyOptimizable = project.costFuncsOK;
        })
        .then(function(response) {

          if (!$scope.isMissingData && $scope.anyOptimizable) {

            rpcService
              .rpcRun(
                'load_progset_summaries', [$scope.state.project.id])
              .then(function(response) {
                $scope.state.progsets = response.data.progsets;

                return rpcService.rpcRun('load_parset_summaries', [$scope.state.project.id]);
              })
              .then(function(response) {
                console.log('reloadActiveProject parsets', response);
                $scope.state.parsets = response.data.parsets;

                return rpcService.rpcRun('load_optimization_summaries', [$scope.state.project.id]);
              })
              .then(function(response) {
                console.log('reloadActiveProject optims', response.data);
                var data = response.data;
                $scope.state.optimizations = data.optimizations;
                $scope.defaultOptimizationsByProgsetId = data.defaultOptimizationsByProgsetId;

                // select an optimization
                $scope.state.optimization = undefined;
                if ($scope.state.optimizations.length > 0) {
                  $scope.setActiveOptimization($scope.state.optimizations[0]);
                  selectDefaultProgsetAndParset($scope.state.optimization);
                }
              });
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
      return _.property('name')(parset);
    }

    function getProgsetName(optimization) {
      var progsetId = optimization.progset_id;
      var progset = _.find($scope.state.progsets, function(progset) {
        return progset.id == progsetId;
      });
      return _.property('name')(progset)
    }

    $scope.checkNotRunnable = function() {
      return !$scope.state.optimization || !$scope.state.optimization.id || !$scope.state.isRunnable;
    };

    $scope.setActiveOptimization = function(optimization) {
      $scope.state.isRunning = false;
      $scope.state.isRunnable = false;
      $scope.state.optimization = optimization;
      $timeout.cancel($scope.state.timer);
      $scope.task_id = makeTaskId();

      // clear screen
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      $scope.state.graphs = {};

      updateOptimizationStatus();
    };

    function makeTaskId() {
      return 'optimize:'
          + $scope.state.project.id + ":"
          + $scope.state.optimization.id;
    }

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
      rpcService
        .rpcRun(
          'save_optimization_summaries',
          [$scope.state.project.id, $scope.state.optimizations])
        .then(function(response) {
          console.log('saveOptimizations response', response);
          loadOptimizations(response.data);
        });
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
      var name = optimization.name;
      copy(rpcService.getUniqueName(name, names));
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
        'Are you sure you want to permanently remove optimization "' + deleteOptimization.name + '"?',
        'Delete optimization'
      );
    };

    $scope.downloadOptimization = function(optimization) {
      rpcService
        .rpcDownload(
          'download_project_object',
          [projectService.project.id, 'optimization', optimization.id])
        .then(function(response) {
          toastr.success('Optimization downloaded');
        });

    };

    $scope.uploadOptimization = function(optimization) {
      rpcService
        .rpcUpload(
          'upload_project_object', [projectService.project.id, 'optimization'], {}, '.opt')
        .then(function(response) {
			if (response.data.name == 'BadFileFormatError') {
			  toastr.error('The file you have chosen is not valid for uploading');  
		    } else {
              toastr.success('Optimization uploaded');
              var name = response.data.name;
              rpcService
                .rpcRun(
                  'load_optimization_summaries', [$scope.state.project.id])
                .then(function(response) {
                  console.log('uploadOptimization response', response);
                  $scope.state.optimizations = response.data.optimizations;
                  $scope.state.optimization = _.findWhere(
                    $scope.state.optimizations, {'name': name});
		        });
			}
        });
    };

    $scope.startOptimization = function() {
      $scope.state.isRunnable = false;
      $scope.state.isRunning = true;
      console.log('startOptimization');
      rpcService
        .rpcAsyncRun(
          'launch_task', [
            $scope.task_id,
            'optimize',
            [
              $scope.state.project.id,
              $scope.state.optimization.id,
              $scope.state.maxtime
            ]
          ])
        .then(function(response) {
          if (response.data.status === 'started') {
            updateOptimizationStatus();
          } else if (response.data.status === 'blocked') {
            $scope.statusMessage = 'Another calculation on this optimization is already running.'
          }
        });
    };

    $scope.cancelOptimization = function() {
      console.log('cancelOptimization');
      $scope.statusMessage = 'Optimization cancelled';
      $timeout.cancel($scope.state.timer);
      $scope.state.isRunnable = true;
      $scope.state.isRunning = false;

      rpcService
        .rpcAsyncRun(
          'cancel_task', [
            $scope.task_id,
          ])
        .then(function(response) {
            console.log('Task cancelled');
        });
    };


    function updateOptimizationStatus() {
      console.log('Updating optimization status');
      rpcService.rpcAsyncRun('check_task', [$scope.task_id])
          .then(function (response) {
            var calcState = response.data;
            if (calcState.status === 'started') {
              $scope.state.isRunnable = false;
              $scope.state.isRunning = true;
              $scope.statusMessage = calcState.status_string;
              $scope.state.timer = $timeout(updateOptimizationStatus, 1000);
            } else {
              $scope.state.isRunnable = true;
              $scope.state.isRunning = false;
              if (calcState.status === 'cancelled') {
                $scope.statusMessage = 'Optimization cancelled';
              } else if (calcState.status === 'completed') {
                $scope.statusMessage = 'Loading graphs...';
                toastr.success('Optimization completed');
                getOptimizationGraphs();
              } else if (calcState.status === 'error') {
                $scope.statusMessage = 'Optimization error';
              } else if (typeof calcState.status === "undefined" || calcState.status === null) {
                console.log('Task status not found');
                $scope.statusMessage = '';
              }
              else {
                console.log(calcState.status);
                $scope.statusMessage = 'Unknown error';
              }
            }
          });
    }

    function getSelectors() {
      function getChecked(s) {
        return s.checked;
      }

      function getKey(s) {
        return s.key
      }

      var scope = $scope.state;
      var which = [];
      if (scope.graphs) {
        if (scope.graphs.advanced) {
          which.push('advanced');
        }
        var selectors = scope.graphs.selectors;
        if (selectors) {
          which = which.concat(_.filter(selectors, getChecked).map(getKey));
        }
      }
      return which;
    }

    function getOptimizationGraphs() {
      if (!$scope.state.optimization.id) {
        return;
      }
      rpcService
        .rpcRun(
          'load_optimization_graphs',
          [$scope.state.project.id, $scope.state.optimization.name, getSelectors()])
        .then(
          function(response) {
            if (response.data.graphs) {
              toastr.success('Graphs loaded');
              $scope.state.graphs = response.data.graphs;
            }
            $scope.state.isRunnable = true;
            $scope.statusMessage = '';
          },
          function(response) {
            console.log('getOptimizationGraphs error', response);
            $scope.state.isRunnable = true;
            toastr.error(response.data);

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
        result.push(_.extend(deepCopyJson(value), {'key': key}));
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

    var optimsScope = $scope;

    function openEditOptimizationModal(optimization) {

      /**
       * The modal converts constraints into a list (as opposed to a dict)
       * to allow angular to iterate through the constraints and
       * to handle changing constraints for different progsets
       */
      function OptimizationModalController($scope, $modalInstance) {

        function initialize() {
          $scope.state = {};
          $scope.state.optimization = angular.copy(optimization);
          $scope.parsets = optimsScope.state.parsets;
          $scope.otherNames = _.without(_.pluck(optimsScope.state.optimizations, 'name'), optimization.name);
          $scope.progsets = optimsScope.state.progsets;
          $scope.cancel = cancel;
          $scope.save = save;
          $scope.isNameClash = isNameClash;
          $scope.checkNotSavable = checkNotSavable;
          $scope.defaultOptimizationsByProgsetId = optimsScope.defaultOptimizationsByProgsetId;
          $scope.selectProgset = selectProgset;
          selectProgset(true);
        }

        function checkNotSavable() {
          var name = $scope.state.optimization.name;
          var result = _.isUndefined(name) || name.trim() === "";
          return result;
        }

        function scaleConstraints(constraints, scale) {
          _.each(constraints, function(constraint) {
            if (constraint.max !== null) {
              constraint.max = constraint.max * scale;
            }
            if (constraint.min !== null) {
              constraint.min = constraint.min * scale;
            }
          });

        }

        function selectProgset(doscale) {
          var progsetId = $scope.state.optimization.progset_id;
          $scope.defaultConstraints = deepCopyJson(
            optimsScope.defaultOptimizationsByProgsetId[progsetId].proporigconstraints);

          var constraints = $scope.state.optimization.proporigconstraints;
          var defaultKeys = _.pluck($scope.defaultConstraints, 'key');
          var constraints = _.filter(
            constraints, function(c) {
              return _.contains(defaultKeys, c.key)
            });
          var constraintKeys = _.pluck(constraints, "key");
          _.each($scope.defaultConstraints, function(constraint) {
            if (!_.contains(constraintKeys, constraint.key)) {
              constraints.push(constraint);
            }
          });
          if (doscale) {
            scaleConstraints(constraints, 100.0);
          }
          $scope.state.optimization.proporigconstraints = constraints;
          console.log("selectProgset constraints", $scope.state.optimization.proporigconstraints);
        }

        function cancel() {
          $modalInstance.dismiss("cancel");
        }

        function save() {
          scaleConstraints($scope.state.optimization.proporigconstraints, 0.01);
          $modalInstance.close($scope.state.optimization);
        }

        function isNameClash(name) {
          return _.contains($scope.otherNames, name);
        }

        initialize();

      }

      $modal
        .open({
          templateUrl: 'js/modules/optimization/optimization-modal.html?cacheBust=xxx',
          controller: OptimizationModalController,
          windowClass: 'fat-modal',
          backdrop: 'static',
          keyboard: false,
        })
        .result
        .then(function(optimization) {
          console.log('save optimization', optimization);
          saveOptimization(optimization);
          $scope.state.optimization = optimization;
        });
    }

    $scope.addOptimization = function(which) {
      var otherNames = _.pluck($scope.state.optimizations, 'name');
      var newOptimization = {
        name: rpcService.getUniqueName('Optimization', otherNames),
        which: which,
        proporigconstraints: {},
      };
      selectDefaultProgsetAndParset(newOptimization);

      var progset_id = newOptimization.progset_id;
      var defaultOptimization = deepCopyJson($scope.defaultOptimizationsByProgsetId[progset_id]);
      newOptimization.objectives = defaultOptimization.objectives[which];
      newOptimization.tvsettings = defaultOptimization.tvsettings; // Warning, would be better to generate this on the backend rather than manually constructing it here!!

      openEditOptimizationModal(newOptimization);
    };

    initialize();

  });

  return module;

});
