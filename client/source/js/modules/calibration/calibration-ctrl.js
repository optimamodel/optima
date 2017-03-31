define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.directive('myEnter', function () {
      return function (scope, element, attrs) {
          element.bind("keydown keypress", function (event) {
              if(event.which === 13) {
                  scope.$apply(function (){
                      scope.$eval(attrs.myEnter);
                  });

                  event.preventDefault();
              }
          });
      };
  });

  module.controller('ModelCalibrationController', function (
      $scope, $http, modalService, $upload,
      $modal, $timeout, toastr, activeProject, projectApi, globalPoller) {

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

      $scope.activeProject = activeProject;
      $scope.$watch('activeProject.project.id', function() {
        reloadActiveProject();
      });

      projectApi
        .getProjectList()
        .then(function() {
          reloadActiveProject();
        });
    }

    function reloadActiveProject() {
      $scope.project =  _.findWhere(
        projectApi.projects, {id: activeProject.project.id});
      if (!$scope.project) {
        return;
      }

      var extrayears = 21;
      $scope.years = _.range($scope.project.startYear, $scope.project.endYear+extrayears);
      var defaultindex = $scope.years.length - extrayears;
      $scope.state.startYear = $scope.years[0];
      $scope.state.endYear = $scope.years[defaultindex];

      console.log("$scope.project", $scope.project);

      // Check if project has spreadsheet uploaded
      $scope.isMissingData = !$scope.project.hasParset;
      if ($scope.isMissingData) {
        return;
      }

      // Fetching list of parsets for open project
      $http
        .get('/api/project/' + $scope.project.id + '/parsets')
        .success(function(response) {
          var parsets = response.parsets;
          if (parsets) {
            $scope.parsets = parsets;
            $scope.state.parset = getMostRecentItem(parsets, 'updated');
            $scope.setActiveParset();
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

    function fetchParameters() {
      return $scope.parameters;
    }

    $scope.getCalibrationGraphs = function() {
      console.log('active parset id', $scope.state.parset.id);
      $http
        .post(
          '/api/project/' + $scope.project.id
          + '/parsets/' + $scope.state.parset.id
          + '/calibration',
          {
            which: getSelectors(),
          })
        .success(function(response) {
          loadParametersAndGraphs(response);
          toastr.success('Loaded graphs');
          console.log('getCalibrationGraphs', response.graphs);
          $scope.statusMessage = '';
          $scope.state.isRunnable = true;
        })
        .error(function() {
          $scope.state.isRunnable = false;
          toastr.error('Error in loading graphs');
        });
    };

    $scope.saveAndUpdateGraphs = function() {
      if (!$scope.parameters) {
        return;
      }
      console.log('saveAndUpdateGraphs', $scope.parameters);
      $http
        .post(
          '/api/project/' + $scope.project.id
          + '/parsets/' + $scope.state.parset.id
          + '/calibration',
          {
            parameters: fetchParameters(),
            which: getSelectors(),
            startYear: $scope.state.startYear,
            endYear: $scope.state.endYear
          })
        .success(function(response) {
          toastr.success('Updated parameters and loaded graphs');
          loadParametersAndGraphs(response);
        });
    };

    $scope.changeParameter = function(parameter) {
      console.log(parameter);
    };

    $scope.addParameterSet = function() {
      function add(name) {
        $http
          .post(
            '/api/project/' + $scope.project.id + '/parsets',
            {name: name})
          .success(function(response) {
            $scope.parsets = response;
            $scope.state.parset = response[response.length - 1];
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
        function copy(name) {
          $http
            .post(
              '/api/project/' + $scope.project.id + '/parsets',
              {
                name: name,
                parset_id: $scope.state.parset.id
              })
            .success(function(response) {
              $scope.parsets = response;
              $scope.state.parset = response[response.length - 1];
              toastr.success('Copied parset');
            });
        }
        var names = _.pluck($scope.parsets, 'name');
        var name = $scope.state.parset.name;
        copy(modalService.getUniqueName(name, names));
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
        $http
          .put(
            '/api/project/' + $scope.project.id
            + '/parsets/' + $scope.state.parset.id,
            {name: name})
          .success(function() {
            $scope.state.parset.name = name;
            toastr.success('Copied parset');
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
        $http
          .delete(
            '/api/project/' + $scope.project.id
            + '/parsets/' + $scope.state.parset.id)
          .success(function() {
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
      $http
        .get(
          '/api/project/' + $scope.project.id
          + '/parsets/' + $scope.state.parset.id
          + '/data',
          {
            headers: {'Content-type': 'application/octet-stream'},
            responseType: 'blob'
          })
        .success(function(response) {
          var blob = new Blob(
            [response], {type: 'application/octet-stream'});
          saveAs(blob, ($scope.state.parset.name + '.par.json'));
        });
    };

    $scope.uploadParameterSet = function() {
      angular
        .element('<input type=\'file\'>')
        .change(function(event) {
          $upload.upload({
            url: '/api/project/' + $scope.project.id
            + '/parsets/' + $scope.state.parset.id
            + '/data',
            file: event.target.files[0]
          }).success(function(response) {
            loadParametersAndGraphs(response);
            $scope.setActiveParset()
          });
        }).click();
    };

    $scope.refreshParset = function() {
      modalService.confirm(
        function () {
          $http
            .post(
              '/api/project/' + $scope.project.id
              + '/refreshparset/' + $scope.state.parset.id)
            .success(function(response) {
              toastr.success('refreshed parameter set')
              loadParametersAndGraphs(response);
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

        globalPoller.stopPolls();

        $scope.state.isRunnable = false;
        $http
          .get(
            '/api/project/' + $scope.project.id
              + '/parsets/' + $scope.state.parset.id
              + '/automatic_calibration')
          .success(function(response) {
            if (response.status === 'started') {
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

    $scope.startAutoCalibration = function() {
      var data = {};
      if ($scope.state.maxtime) {
        data.maxtime = Number($scope.state.maxtime);
      }
      $http
        .post(
          '/api/project/' + $scope.project.id
            + '/parsets/' + $scope.state.parset.id
            + '/automatic_calibration',
          data)
        .success(function(response) {
          if (response.status === 'started') {
            $scope.statusMessage = 'Autofit started.';
            $scope.secondsRun = 0;
            initPollAutoCalibration();
          } else if (response.status === 'blocked') {
            $scope.statusMessage = 'Another calculation on this project is already running.'
          }
        })
    };

    function initPollAutoCalibration() {
      globalPoller.startPoll(
        $scope.state.parset.id,
        '/api/project/' + $scope.project.id
          + '/parsets/' + $scope.state.parset.id
          + '/automatic_calibration',
        function (response) {
          if (response.status === 'completed') {
            $scope.statusMessage = '';
            toastr.success('Autofit completed');
            $scope.getCalibrationGraphs();
          } else if (response.status === 'started') {
            var start = new Date(response.start_time);
            var now = new Date(response.current_time);
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
});
