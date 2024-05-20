define(['angular', 'underscore'], function (angular, _) {

  'use strict';


  var module = angular.module('app.calibration', ['ui.router']);


  module.config(function ($stateProvider) {
    $stateProvider
        .state('calibration', {
          url: '/calibration',
          templateUrl: 'js/modules/calibration/calibration.html?cacheBust=xxx',
          controller: 'ModelCalibrationController',
        })
  });


  module.controller('ModelCalibrationController', function (
      $scope, modalService, rpcService, $modal, $timeout, toastr,
      projectService) {

    function initialize() {
      $scope.parsets = [];
      $scope.state = {
        maxtime: 10,
        isRunnable: false,
        isRunning: false,
        parset: undefined,
        startYear: 1900,
        endYear: 2030,
        graphs: undefined,
        advancedPars: false,
        timer: null,
      };

      $scope.$on('$destroy', function () {
        $timeout.cancel($scope.state.timer);
      });

      // Load the active project, telling the function we're not using an Undo stack.
      reloadActiveProject(false);

      $scope.projectService = projectService;
      $scope.$watch('projectService.project.id', function () {
        if (!_.isUndefined($scope.project) && ($scope.project.id !== projectService.project.id)) {
          reloadActiveProject(false);  // we're not using an Undo stack here, either
        }
      });
    }

    function reloadActiveProject(useUndoStack) {
      projectService
          .getActiveProject()
          .then(function (response) {
            $scope.project = response.data;
            if (!$scope.project) {
              return;
            }
            $scope.isMissingData = !$scope.project.calibrationOK;
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
                .then(function (response) {
                  var parsets = response.data.parsets;
                  if (parsets) {
                    $scope.parsets = parsets;
                    $scope.state.parset = getMostRecentItem(parsets, 'updated');
                    $scope.setActiveParset();
                  }
                });

            // Initialize a new UndoStack on the server if we are not using an UndoStack in this
            // call.
            if (!useUndoStack) {
              rpcService
                  .rpcRun(
                      'init_new_undo_stack', [$scope.project.id]);
            }
          });
    }

    $scope.isNumberKey = function (evt) {
      var charCode = (evt.which) ? evt.which : event.keyCode;
      return !(charCode > 31 && (charCode < 48 || charCode > 57));
    };

    function getMostRecentItem(aList, datetimeProp) {
      var aListByDate = _.sortBy(aList, function (item) {
        return new Date(item[datetimeProp]);
      });
      var iLast = aListByDate.length - 1;
      return aListByDate[iLast];
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

    function loadParametersAndGraphs(response) {
      $scope.state.graphs = response.graphs;
      $scope.parameters = angular.copy(response.parameters);
    }

    $scope.getCalibrationGraphs = function () {
      console.log('active parset id', $scope.state.parset.id);
      var rpc_args =
          [
            projectService.project.id,
            $scope.state.parset.id,
            "calibration",
            getSelectors(),
            null,
            $scope.state.advancedPars
          ];
      rpcService
          .rpcRun('load_parset_graphs', rpc_args)
          .then(
              function (response) {
                loadParametersAndGraphs(response.data);
                toastr.success('Loaded graphs');
                console.log('getCalibrationGraphs', response.graphs);
                rpcService
                    .rpcRun('get_isfixed', [projectService.project.id, $scope.state.parset.id])
                    .then(function (response) {
                      var isfixed = response.data.isfixed;
                      if (isfixed) {
                        document.getElementById("ARTProportion").checked = true;
                      } else {
                        document.getElementById("ARTConstant").checked = true;
                      }
                    });
              },
              function (response) {
                toastr.error('Error in loading graphs');
              });
    };

    $scope.saveAndUpdateGraphs = function () {
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
                $scope.parameters,
                $scope.state.advancedPars
              ],
              {
                startYear: $scope.state.startYear,
                endYear: $scope.state.endYear
              })
          .then(
              function (response) {
                loadParametersAndGraphs(response.data);
                toastr.success('Loaded graphs');
                console.log('saveAndUpdateGraphs', response.graphs);
                rpcService
                    .rpcRun(
                        'push_project_to_undo_stack',
                        [projectService.project.id]);
              },
              function (response) {
                toastr.error('Error in loading graphs');
              });
    };

    $scope.changeParameter = function (parameter) {
      console.log(parameter);
    };

    $scope.toggleAdvancedPars = function () {
      $scope.state.advancedPars = !$scope.state.advancedPars; // Do the actual toggle
      console.log('toggleAdvancedPars', $scope.state.advancedPars);
      $scope.saveAndUpdateGraphs(); // Update the graphs
    };

    $scope.addParameterSet = function () {
      function add(name) {
        rpcService
            .rpcRun(
                'create_parset', [projectService.project.id, name])
            .then(function (response) {
              $scope.parsets = response.data.parsets;
              $scope.state.parset = $scope.parsets[$scope.parsets.length - 1];
              toastr.success('Created parset');
              $scope.setActiveParset();
              rpcService
                  .rpcRun(
                      'push_project_to_undo_stack',
                      [projectService.project.id]);
            });
      }

      modalService.rename(
          add, 'Add parameter set', 'Enter name', '',
          'Name already exists',
          _.pluck($scope.parsets, 'name'));
    };

    $scope.copyParameterSet = function () {
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
            .then(function (response) {
              $scope.parsets = response.data.parsets;
              $scope.state.parset = $scope.parsets[$scope.parsets.length - 1];
              toastr.success('Copied parset');
              rpcService
                  .rpcRun(
                      'push_project_to_undo_stack',
                      [projectService.project.id]);
            });
      }
    };

    $scope.renameParameterSet = function () {
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
            .then(function (response) {
              $scope.state.parset.name = name;
              toastr.success('Renamed parset');
              rpcService
                  .rpcRun(
                      'push_project_to_undo_stack',
                      [projectService.project.id]);
            });
      }

      modalService.rename(
          rename, 'Rename parameter set', 'Enter name',
          $scope.state.parset.name,
          'Name already exists',
          _.without(_.pluck($scope.parsets, 'name'), $scope.state.parset.name));
    };


    $scope.deleteParameterSet = function () {
      if (!$scope.state.parset) {
        modalService.informError(
            [{message: 'No parameter set selected.'}]);
        return;
      }

      if ($scope.parsets.length < 2) {
        modalService.informError(
            [{message: 'Deleting the only parameter set is not permitted.'}]);
        return;
      }

      function remove() {
        rpcService
            .rpcRun(
                'delete_parset',
                [projectService.project.id, $scope.state.parset.id])
            .then(function (response) {
              $scope.parsets = _.filter(
                  $scope.parsets, function (parset) {
                    return parset.id !== $scope.state.parset.id;
                  }
              );
              if ($scope.parsets.length > 0) {
                $scope.state.parset = $scope.parsets[0];
                toastr.success('Deleted parset');
                $scope.setActiveParset();
                rpcService
                    .rpcRun(
                        'push_project_to_undo_stack',
                        [projectService.project.id]);
              }
            });
      }

      modalService.confirm(
          remove,
          function () {
          },
          'Yes, remove this parameter set',
          'No',
          'Are you sure you want to permanently remove parameter set "'
          + $scope.state.parset.name + '"?',
          'Delete parameter set'
      );
    };

    $scope.downloadParameterSet = function () {
      rpcService
          .rpcDownload(
              'download_project_object',
              [projectService.project.id, 'parset', $scope.state.parset.id])
          .then(function (response) {
            toastr.success('Parameter set downloaded');
          });
    };

    $scope.uploadParameterSet = function () {
      console.log('uploadParameterSet');
      rpcService
          .rpcUploadSerial(
              'upload_project_object', [$scope.project.id, 'parset'], {}, '.par')
          .then(function (response) {
            if (response.data.name == 'BadFileFormatError') {
              toastr.error('The file you have chosen is not valid for uploading');
            } else {
              toastr.success('Parameter set uploaded');
              var name = response.data.name;

              rpcService
                  .rpcRun('load_parset_summaries', [$scope.project.id])
                  .then(function (response) {
                    var parsets = response.data.parsets;
                    if (parsets) {
                      $scope.parsets = parsets;
                      $scope.state.parset = _.findWhere($scope.parsets, {name: name});
                      $scope.setActiveParset();
                      rpcService
                          .rpcRun(
                              'push_project_to_undo_stack',
                              [projectService.project.id]);
                    }
                  });
            }
          });
    };

    $scope.refreshParameterSet = function () {
      rpcService
          .rpcRun(
              'refresh_parset', [projectService.project.id, $scope.state.parset.id])
          .then(function (response) {
            toastr.success('Parameter set refreshed from data');
            $scope.getCalibrationGraphs();
            rpcService
                .rpcRun(
                    'push_project_to_undo_stack',
                    [projectService.project.id]);
          });
    };

    $scope.refreshParameterSet = function () {
      function refreshparset(initialprev) {
        rpcService
            .rpcRun(
                'refresh_parset', [projectService.project.id, $scope.state.parset.id, initialprev])
            .then(function (response) {
              toastr.success('Parameter set refreshed from data');
              $scope.getCalibrationGraphs();
              rpcService
                  .rpcRun(
                      'push_project_to_undo_stack',
                      [projectService.project.id]);
            });
      }

      // Because passing arguments is too hard -- to supply the options for the choice below
      function refreshparsetandprev() {
        refreshparset(true);
      }

      function refreshparsetwithoutprev() {
        refreshparset(false);
      }

      modalService.choice(
          refreshparsetandprev,
          refreshparsetwithoutprev,
          'Use the values from the uploaded spreadsheet',
          'Use the values entered in the calibration',
          'What values would you like to use to for initial HIV prevalence?',
          'Reload values from spreadsheet to this parameter set'
      );
    };

    $scope.constantProportionART = function () {
      rpcService
          .rpcRun(
              'fixproptx_on',
              [
                projectService.project.id,
                $scope.state.parset.id])
          .then(function (response) {
            toastr.success('Using constant proportion on ART');
            $scope.getCalibrationGraphs();
            rpcService
                .rpcRun(
                    'push_project_to_undo_stack',
                    [projectService.project.id]);
          });
    };

    $scope.constantNumberART = function () {
      rpcService
          .rpcRun(
              'fixproptx_off',
              [
                projectService.project.id,
                $scope.state.parset.id])
          .then(function (response) {
            toastr.success('Using constant number on ART');
            $scope.getCalibrationGraphs();
            rpcService
                .rpcRun(
                    'push_project_to_undo_stack',
                    [projectService.project.id]);
          });
    };

    $scope.undo = function () {
      rpcService
          .rpcRun(
              'fetch_undo_project',
              [projectService.project.id])
          .then(function (response) {
            if (response.data.didundo)
              reloadActiveProject(true);
          });
    }

    $scope.redo = function () {
      rpcService
          .rpcRun(
              'fetch_redo_project',
              [projectService.project.id])
          .then(function (response) {
            if (response.data.didredo)
              reloadActiveProject(true);
          });
    }

    // autofit routines

    $scope.checkNotRunnable = function () {
      return !$scope.state.parset || !$scope.state.parset.id || !$scope.state.isRunnable;
    };

    $scope.setActiveParset = function () {
      $scope.state.isRunning = false;
      $scope.state.isRunnable = false;
      if ($scope.state.parset.id) {
        $timeout.cancel($scope.state.timer);
        $scope.task_id = makeTaskId();
        $scope.getCalibrationGraphs(); // Render any existing figures
        updateCalibrationStatus(true); // Update status
      }
    };

    function makeTaskId() {
      return "autofit:"
          + projectService.project.id + ":"
          + $scope.state.parset.id;
    }

    $scope.startAutoCalibration = function () {
      $scope.state.isRunnable = false;
      $scope.state.isRunning = true;
      console.log('startAutoCalibration');
      rpcService
          .rpcAsyncRun(
              'launch_task', [
                $scope.task_id,
                'autofit',
                [
                  projectService.project.id,
                  $scope.state.parset.id,
                  $scope.state.maxtime
                ]
              ])
          .then(function (response) {
            if (response.data.status === 'started') {
              updateCalibrationStatus();
            } else if (response.data.status === 'blocked') {
              $scope.statusMessage = 'Another calculation on this project is already running.'
            }
          });
    };

    $scope.cancelAutoCalibration = function () {
      console.log('cancelAutoCalibration');
      $scope.statusMessage = 'Calibration cancelled';
      $timeout.cancel($scope.state.timer);
      $scope.state.isRunnable = true;
      $scope.state.isRunning = false;

      rpcService
          .rpcAsyncRun(
              'cancel_task', [
                $scope.task_id,
              ])
          .then(function (response) {
            console.log('Task cancelled');
          });
    };

    function updateCalibrationStatus(noRender) {
      // the noRender flag is provided because this function gets called when the user changes the parset
      // In that case, any pre-rendered figures are displayed, followed by updating the calibration status
      // If a calibration is ongoing, then it will continue and be rendered as soon as it is completed
      // If a calibration has already completed, then we would have already rendered the same graphs that get
      // rendered on completion, so we don't need to render them a second time.
      console.log('Updating calibration status');
      rpcService.rpcAsyncRun('check_task', [$scope.task_id])
          .then(function (response) {
            var calcState = response.data;
            if (calcState.status === 'started') {
              $scope.state.isRunnable = false;
              $scope.state.isRunning = true;
              $scope.statusMessage = calcState.status_string;
              $scope.state.timer = $timeout(updateCalibrationStatus, 1000);
            } else {
              $scope.state.isRunnable = true;
              $scope.state.isRunning = false;
              if (calcState.status === 'cancelled') {
                $scope.statusMessage = 'Calibration cancelled';
              } else if (calcState.status === 'completed') {
                toastr.success('Calibration completed');
                if(typeof noRender === 'undefined'){ // the noRender flag just gets passed in by setActiveParset
                  $scope.statusMessage = 'Loading graphs...';
                  $scope.getCalibrationGraphs();
                  $scope.statusMessage = '';
                }
                rpcService.rpcRun('push_project_to_undo_stack',[projectService.project.id]);
              } else if (calcState.status === 'error') {
                $scope.statusMessage = 'Calibration error';
              } else if (typeof calcState.status === "undefined" || calcState.status === null) {
                console.log('Task status not found');
                $scope.statusMessage = '';
              } else {
                console.log(calcState.status);
                $scope.statusMessage = 'Unknown error';
              }
            }
          });
    }

    initialize();

  });

  return module;
});
