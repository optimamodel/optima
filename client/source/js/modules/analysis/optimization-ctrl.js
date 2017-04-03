define(
  ['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('AnalysisOptimizationController', function (
      $scope, $http, $upload, $modal, toastr, modalService,
      activeProject, projectApi, $timeout, globalPoller) {

    function initialize() {

      $scope.state = {
        project: null,
        maxtime: 10,
        isRunnable: false,
        graphs: undefined,
        optimizations: [],
        years: null,
        start: null,
        end: null
      };

      $scope.editOptimization = openEditOptimizationModal;
      $scope.getParsetName = getParsetName;
      $scope.getProgsetName = getProgsetName;

      $scope.anyOptimizable = false;

      $scope.activeProject = activeProject;
      $scope.$watch('activeProject.project.id', function() {
        reloadActiveProject();
      });

      reloadActiveProject();
    }

    function reloadActiveProject() {
      projectApi
        .getActiveProject()
        .then(function(response) {
          var project = response.data;
          $scope.state.project = project;
          $scope.state.years = _.range(project.startYear, project.endYear + 1);
          $scope.state.start = project.startYear;
          $scope.state.end = project.endYear;
          $scope.isMissingData = !project.hasParset;

          return $http.get('/api/project/' + $scope.state.project.id + '/optimizable');
        })
        .then(function(response) {
          $scope.anyOptimizable = response.data;

          if (!$scope.isMissingData && $scope.anyOptimizable) {
            $http
              .get('/api/project/' + $scope.state.project.id + '/progsets')
              .then(function(response) {
                $scope.state.progsets = response.data.progsets;
                return $http.get('/api/project/' + $scope.state.project.id + '/parsets');
              })
              .then(function(response) {
                $scope.state.parsets = response.data.parsets;
                return $http.get('/api/project/' + $scope.state.project.id + '/optimizations')
              })
              .then(function(response) {
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
      var progsetId = optimization.progset_id;
      var progset = _.find($scope.state.progsets, function(progset) {
        return progset.id == progsetId;
      });
      return progset.name
    }

    $scope.checkNotRunnable = function() {
      return !$scope.state.optimization || !$scope.state.optimization.id || !$scope.state.isRunnable;
    };

    $scope.setActiveOptimization = function(optimization) {
      $scope.state.optimization = optimization;
      selectOptimization();
    };

    function selectOptimization() {
      globalPoller.stopPolls();

      $scope.state.isRunnable = false;
      var optimization = $scope.state.optimization;

      // clear screen
      $scope.optimizationCharts = [];
      $scope.selectors = [];
      $scope.state.graphs = {};
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

    $scope.startOptimization = function(optimization) {
      $scope.state.isRunnable = false;
      $http
        .post(
          '/api/project/' + $scope.state.project.id
            + '/optimizations/' + optimization.id
            + '/results',
          {
            maxtime: $scope.state.maxtime,
            start: $scope.state.start,
            end: $scope.state.end
          })
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
      function getChecked(s) { return s.checked; }
      function getKey(s) { return s.key }
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
      $http
        .post(
          '/api/project/' + $scope.state.project.id
            + '/optimizations/' + $scope.state.optimization.id
            + '/graph',
          {which: getSelectors()})
        .success(function (response) {
          if (response.graphs) {
            toastr.success('Graphs loaded');
            $scope.state.graphs = response.graphs;
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
      return swapKeysOfDictOfDict(convertToDict(listOfConstraints));
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
          $scope.state.optimization.constraints = listifyConstraints(
            $scope.state.optimization.constraints);
          $scope.parsets = optimsScope.state.parsets;
          $scope.otherNames = _.without(_.pluck(optimsScope.state.optimizations, 'name'), optimization.name);
          $scope.progsets = optimsScope.state.progsets;
          $scope.cancel = cancel;
          $scope.save = save;
          $scope.isNameClash = isNameClash;
          $scope.checkNotSavable = checkNotSavable;
          $scope.defaultOptimizationsByProgsetId = optimsScope.defaultOptimizationsByProgsetId;
          $scope.selectProgset = selectProgset;
          selectProgset();
        }

        function checkNotSavable() {
          var name = $scope.state.optimization.name;
          var result = _.isUndefined(name) || name.trim() === "";
          return result;
        }

        function scaleConstraints(constraints, scale) {
          _.each(constraints, function(constraint) {
            if (constraint.max !== null) {
              constraint.max = constraint.max*scale;
            }
            if (constraint.min !== null) {
              constraint.min = constraint.min*scale;
            }
          });

        }

        function selectProgset() {
          var progsetId = $scope.state.optimization.progset_id;
          $scope.defaultConstraints = listifyConstraints(
            deepCopyJson(optimsScope.defaultOptimizationsByProgsetId[progsetId].constraints));

          var constraints = $scope.state.optimization.constraints;
          var defaultKeys = _.pluck($scope.defaultConstraints, 'key');
          var constraints = _.filter(
            constraints, function(c) { return _.contains(defaultKeys, c.key)});
          var constraintKeys = _.pluck(constraints, "key");
          _.each($scope.defaultConstraints, function(constraint) {
            if (!_.contains(constraintKeys, constraint.key)) {
              constraints.push(constraint);
            }
          });
          constraints = _.sortBy(constraints, function(c) { return c.key });
          scaleConstraints(constraints, 100.0)
          $scope.state.optimization.constraints = constraints;
          console.log("selectProgset constraints", $scope.state.optimization.constraints);
        }

        function cancel() { $modalInstance.dismiss("cancel"); }

        function save() {
          scaleConstraints($scope.state.optimization.constraints, 0.01);
          $scope.state.optimization.constraints = revertToConstraints(
            $scope.state.optimization.constraints);
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
      var otherNames = _.pluck($scope.state.optimizations, 'name');
      var newOptimization = {
        name: modalService.getUniqueName('Optimization', otherNames),
        which: which,
        constraints: {},
      };
      selectDefaultProgsetAndParset(newOptimization);

      var progset_id = newOptimization.progset_id;
      var defaultOptimization = deepCopyJson($scope.defaultOptimizationsByProgsetId[progset_id]);
      newOptimization.objectives = defaultOptimization.objectives[which];

      openEditOptimizationModal(newOptimization);
    };

    initialize();

  });
});


