define(['angular', 'underscore'], function (angular, _) {

  'use strict';


  var module = angular.module('app.model', ['ui.router']);


  module.config(function ($stateProvider) {
      $stateProvider
        .state('calibration', {
          url: '/calibration',
          templateUrl: 'js/modules/calibration/calibration.html',
          controller: 'ModelCalibrationController',
        })
    });


  module.controller('ModelCalibrationController', function (
      $scope, modalService, rpcService, $modal, $timeout, toastr,
      projectService, pollerService) {

    function initialize() {
      $scope.parsets = [];
      $scope.state = {
        maxtime: '10',
        isRunnable: false,
        parset: undefined,
        startYear: 1900,
        endYear: 2020,
        graphs: undefined,
      };

      reloadActiveProject();

      $scope.projectService = projectService;
      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined($scope.project) && ($scope.project.id !== projectService.project.id)) {
          reloadActiveProject();
        }
      });
    }

    function reloadActiveProject() {
      projectService
        .getActiveProject()
        .then(function(response) {
          $scope.project = response.data;
          if (!$scope.project) {
            return;
          }
          $scope.isMissingData = !$scope.project.hasParset;
          if ($scope.isMissingData) {
            return;
          }

          console.log("reloadActiveProject project", $scope.project.name);
          var extrayears = 21;
          $scope.years = _.range($scope.project.startYear, $scope.project.endYear + extrayears);
          var defaultindex = $scope.years.length - extrayears;
          $scope.state.startYear = $scope.years[0];
          $scope.state.endYear = $scope.years[defaultindex];

          // Fetching list of parsets for open project
          rpcService
            .rpcRun(
              'load_parset_summaries', [$scope.project.id])
            .then(function(response) {
              var parsets = response.data.parsets;
              if (parsets) {
                $scope.parsets = parsets;
                $scope.state.parset = getMostRecentItem(parsets, 'updated');
                $scope.setActiveParset();
              }
            });
        });
    }

    $scope.isNumberKey = function(evt) {
        var charCode = (evt.which) ? evt.which : event.keyCode;
        return !(charCode > 31 && (charCode < 48 || charCode > 57));
    };

    function getMostRecentItem(aList, datetimeProp) {
      var aListByDate = _.sortBy(aList, function(item) {
        return new Date(item[datetimeProp]);
      });
      var iLast = aListByDate.length - 1;
      return aListByDate[iLast];
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

    function loadParametersAndGraphs(response) {
      $scope.state.graphs = response.graphs;
      $scope.parameters = angular.copy(response.parameters);
    }

    $scope.getCalibrationGraphs = function() {
      console.log('active parset id', $scope.state.parset.id);
      rpcService
        .rpcRun(
          'load_parset_graphs',
          [projectService.project.id, $scope.state.parset.id,
          "calibration", getSelectors()])
        .then(
          function(response) {
            loadParametersAndGraphs(response.data);
            toastr.success('Loaded graphs');
            console.log('getCalibrationGraphs', response.graphs);
            $scope.statusMessage = '';
            $scope.state.isRunnable = true;
          },
          function(response) {
            $scope.state.isRunnable = false;
            toastr.error('Error in loading graphs');
          });
    };

    $scope.saveAndUpdateGraphs = function() {
      if (!$scope.parameters) {
        return;
      }
      console.log('saveAndUpdateGraphs', $scope.parameters);
      rpcService
        .rpcRun(
          'load_parset_graphs',
          [
            projectService.project.id,
            $scope.state.parset.id,
            "calibration",
            getSelectors(),
            $scope.parameters
          ],
          {
            startYear: $scope.state.startYear,
            endYear: $scope.state.endYear
          })
        .then(
          function(response) {
            loadParametersAndGraphs(response.data);
            toastr.success('Loaded graphs');
            console.log('getCalibrationGraphs', response.graphs);
            $scope.statusMessage = '';
            $scope.state.isRunnable = true;
          },
          function(response) {
            $scope.state.isRunnable = false;
            toastr.error('Error in loading graphs');
          });
    };

    $scope.changeParameter = function(parameter) {
      console.log(parameter);
    };

    $scope.addParameterSet = function() {
      function add(name) {
        rpcService
          .rpcRun(
            'create_parset', [projectService.project.id, name])
          .then(function(response) {
            $scope.parsets = response.data.parsets;
            $scope.state.parset = $scope.parsets[$scope.parsets.length - 1];
            toastr.success('Created parset');
            $scope.setActiveParset();
          });
      }
      modalService.rename(
        add, 'Add parameter set', 'Enter name', '',
        'Name already exists',
        _.pluck($scope.parsets, 'name'));
    };

    $scope.copyParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
      } else {
        var names = _.pluck($scope.parsets, 'name');
        var name = $scope.state.parset.name;
        var newName = rpcService.getUniqueName(name, names);
        rpcService
          .rpcRun(
            'copy_parset',
            [
              projectService.project.id,
              $scope.state.parset.id,
              newName])
          .then(function(response) {
            $scope.parsets = response.data.parsets;
            $scope.state.parset = $scope.parsets[$scope.parsets.length - 1];
            toastr.success('Copied parset');
          });
      }
    };

    $scope.renameParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
        return;
      }

      if ($scope.state.parset.name === "default") {
        modalService.informError(
          [{message: 'Renaming the default parameter set is not permitted.'}]);
        return;
      }

      function rename(name) {
        rpcService
          .rpcRun(
            'rename_parset',
            [
              projectService.project.id,
              $scope.state.parset.id,
              name])
          .then(function(response) {
            $scope.state.parset.name = name;
            toastr.success('Renamed parset');
          });
      }

      modalService.rename(
        rename, 'Rename parameter set', 'Enter name',
        $scope.state.parset.name,
        'Name already exists',
        _.without(_.pluck($scope.parsets, 'name'), $scope.state.parset.name));
    };


    $scope.deleteParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
        return;
      }

      if ($scope.state.parset.name === "default") {
        modalService.informError(
          [{message: 'Deleting the default parameter set is not permitted.'}]);
        return;
      }

      function remove() {
        rpcService
          .rpcRun(
            'delete_parset',
            [projectService.project.id, $scope.state.parset.id])
          .then(function(response) {
            $scope.parsets = _.filter(
              $scope.parsets, function(parset) {
                return parset.id !== $scope.state.parset.id;
              }
            );
            if ($scope.parsets.length > 0) {
              $scope.state.parset = $scope.parsets[0];
              toastr.success('Deleted parset');
              $scope.setActiveParset();
            }
          });
      }

      modalService.confirm(
        remove,
        function() {
        },
        'Yes, remove this parameter set',
        'No',
        'Are you sure you want to permanently remove parameter set "'
        + $scope.state.parset.name + '"?',
        'Delete parameter set'
      );
    };

    $scope.downloadParameterSet = function() {
      rpcService
        .rpcDownload(
          'download_project_object',
          [projectService.project.id, 'parset', $scope.state.parset.id])
        .then(function(response) {
          toastr.success('Parset downloaded');
        });
    };

    $scope.uploadParameterSet = function() {
      console.log('uploadParameterSet');
      rpcService
        .rpcUpload(
          'upload_project_object', [$scope.project.id, 'parset'], {}, '.par')
        .then(function(response) {
          toastr.success('Parset uploaded');
          var name = response.data.name;

          rpcService
            .rpcRun('load_parset_summaries', [$scope.project.id])
            .then(function(response) {
              var parsets = response.data.parsets;
              if (parsets) {
                $scope.parsets = parsets;
                $scope.state.parset = _.findWhere($scope.parsets, {name: name});
                $scope.setActiveParset();
              }
            });
        });
    };

    $scope.refreshParset = function() {
      modalService.confirm(
        function () {
          rpcService
            .rpcRun(
              'refresh_parset', [projectService.project.id, $scope.state.parset.id])
            .then(function(response) {
              toastr.success('Parset uploaded');
              $scope.getCalibrationGraphs();
            });
        },
        function () { },
        'Yes',
        'No',
        'This will reset all your calibration parameters to match the ones in the "default" parset. Do you wish to continue?',
        'Refresh paramter set'
      );
    };

    // autofit routines

    $scope.checkNotRunnable = function() {
      return !$scope.state.parset || !$scope.state.parset.id || !$scope.state.isRunnable;
    };

    $scope.setActiveParset = function() {
      if ($scope.state.parset.id) {
        pollerService.stopPolls();
        $scope.state.isRunnable = false;
        rpcService
          .rpcAsyncRun(
            'check_if_task_started', [makeTaskId()])
          .then(function(response) {
            var status = response.data.status;
            if (status === 'started') {
              initPollAutoCalibration();
            } else {
              $scope.statusMessage = 'Checking for pre-calculated figures...';
              $scope.getCalibrationGraphs();
            }
          });
      } else {
        $scope.state.isRunnable = true;
      }
    };

    function makeTaskId() {
      return "autofit:"
        + projectService.project.id + ":"
        + $scope.state.parset.id;
    }

    $scope.startAutoCalibration = function() {
      rpcService
        .rpcAsyncRun(
          'launch_task',
          [
            makeTaskId(),
            'autofit',
            [
              projectService.project.id,
              $scope.state.parset.id,
              $scope.state.maxtime
            ]
          ])
        .then(function(response) {
          var status = response.data.status;
          if (status === 'started') {
            $scope.statusMessage = 'Autofit started.';
            $scope.secondsRun = 0;
            initPollAutoCalibration();
          } else if (status === 'blocked') {
            $scope.statusMessage = 'Another calculation on this project is already running.'
          }
        });

      // rpcService
      //   .rpcAsyncRun(
      //     'launch_autofit',
      //     [projectService.project.id, $scope.state.parset.id, $scope.state.maxtime])
      //   .then(function(response) {
      //     var status = response.data.status;
      //     if (status === 'started') {
      //       $scope.statusMessage = 'Autofit started.';
      //       $scope.secondsRun = 0;
      //       initPollAutoCalibration();
      //     } else if (status === 'blocked') {
      //       $scope.statusMessage = 'Another calculation on this project is already running.'
      //     }
      //   });
    };

    function initPollAutoCalibration() {
      // var taskId = 'autofit-' + $scope.state.parset.id;
      var taskId = makeTaskId();
      pollerService.startPollForRpc(
        projectService.project.id,
        taskId,
        function (response) {
          var status = response.data.status;
          if (status === 'completed') {
            $scope.statusMessage = '';
            toastr.success('Autofit completed');
            $scope.getCalibrationGraphs();
          } else if (status === 'started') {
            var start = new Date(response.data.start_time);
            var now = new Date(response.data.current_time);
            var diff = now.getTime() - start.getTime();
            var seconds = parseInt(diff / 1000);
            $scope.statusMessage = "Autofit running for " + seconds + " s";
          } else {
            $scope.statusMessage = 'Autofit failed';
            $scope.state.isRunnable = true;
          }
        }
      );
    }

    initialize();

  });

  return module;
});
