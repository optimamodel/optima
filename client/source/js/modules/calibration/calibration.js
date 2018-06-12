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
      projectService, pollerService) {

    function initialize() {
      $scope.parsets = [];
      $scope.state = {
        maxtime: 10,
        isRunnable: false,
        parset: undefined,
        startYear: 1900,
        endYear: 2020,
        graphs: undefined,
        advancedPars: false
      };

	  // Load the active project, telling the function we're not using an Undo stack.
      reloadActiveProject(false);

      $scope.projectService = projectService;
      $scope.$watch('projectService.project.id', function() {
        if (!_.isUndefined($scope.project) && ($scope.project.id !== projectService.project.id)) {
          reloadActiveProject(false);  // we're not using an Undo stack here, either
        }
      });
    }

    function reloadActiveProject(useUndoStack) {
      projectService
        .getActiveProject()
        .then(function(response) {
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
            .then(function(response) {
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
            $scope.parameters,
            $scope.state.advancedPars
          ],
          {
            startYear: $scope.state.startYear,
            endYear: $scope.state.endYear
          })
        .then(
          function(response) {
            loadParametersAndGraphs(response.data);
            toastr.success('Loaded graphs');
            console.log('saveAndUpdateGraphs', response.graphs);
            $scope.statusMessage = '';
            $scope.state.isRunnable = true;
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [projectService.project.id]);
          },
          function(response) {
            $scope.state.isRunnable = false;
            toastr.error('Error in loading graphs');
          });
    };

    $scope.changeParameter = function(parameter) {
      console.log(parameter);
    };

    $scope.toggleAdvancedPars = function() {
      $scope.state.advancedPars = !$scope.state.advancedPars; // Do the actual toggle
      console.log('toggleAdvancedPars', $scope.state.advancedPars);
      $scope.saveAndUpdateGraphs(); // Update the graphs
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
            rpcService
              .rpcRun(
                'push_project_to_undo_stack',
                [projectService.project.id]);
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


    $scope.deleteParameterSet = function() {
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
              rpcService
                .rpcRun(
                  'push_project_to_undo_stack',
                  [projectService.project.id]);
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
          toastr.success('Parameter set downloaded');
        });
    };

    $scope.uploadParameterSet = function() {
      console.log('uploadParameterSet');
      rpcService
        .rpcUpload(
          'upload_project_object', [$scope.project.id, 'parset'], {}, '.par')
        .then(function(response) {
		  if (response.data.name == 'BadFileFormatError') {
			toastr.error('The file you have chosen is not valid for uploading');  
		  } else {
            toastr.success('Parameter set uploaded');
            var name = response.data.name;

            rpcService
              .rpcRun('load_parset_summaries', [$scope.project.id])
              .then(function(response) {
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

    $scope.refreshParameterSet = function() {
      rpcService
        .rpcRun(
          'refresh_parset', [projectService.project.id, $scope.state.parset.id])
        .then(function(response) {
          toastr.success('Parameter set refreshed from data');
          $scope.getCalibrationGraphs();
          rpcService
            .rpcRun(
              'push_project_to_undo_stack',
              [projectService.project.id]);
        });
    };

    $scope.refreshParameterSet = function() {
      function refreshparset(initialprev) {
        rpcService
          .rpcRun(
            'refresh_parset', [projectService.project.id, $scope.state.parset.id, initialprev])
          .then(function(response) {
            $scope.state.parset.name = name;
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

    $scope.constantProportionART = function() {
      rpcService
        .rpcRun(
          'fixproptx_on',
          [
            projectService.project.id,
            $scope.state.parset.id])
        .then(function(response) {
          toastr.success('Using constant proportion on ART');
          $scope.getCalibrationGraphs();
          rpcService
            .rpcRun(
              'push_project_to_undo_stack',
              [projectService.project.id]);
        });
    };

    $scope.constantNumberART = function() {
      rpcService
        .rpcRun(
          'fixproptx_off',
          [
            projectService.project.id,
            $scope.state.parset.id])
        .then(function(response) {
          toastr.success('Using constant number on ART');
          $scope.getCalibrationGraphs();
          rpcService
            .rpcRun(
              'push_project_to_undo_stack',
              [projectService.project.id]);
        });
    };

	$scope.undo = function() {
      rpcService
        .rpcRun(
          'fetch_undo_project',
          [projectService.project.id])
        .then(function(response) {
		  if (response.data.didundo)
		    reloadActiveProject(true);
        });		
	}
	
	$scope.redo = function() {
      rpcService
        .rpcRun(
          'fetch_redo_project',
          [projectService.project.id])
        .then(function(response) {
		  if (response.data.didredo)
		    reloadActiveProject(true);		  
        });      		
	}
	
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
			rpcService
			  .rpcRun(
			    'push_project_to_undo_stack', 
				[projectService.project.id]);
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
