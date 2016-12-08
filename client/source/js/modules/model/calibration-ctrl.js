define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller('ModelCalibrationController', function (
      $scope, $http, info, modalService, $upload,
      $modal, $timeout, toastr, globalPoller, renameModalService) {

    var project = info.data;

    function initialize() {

      $scope.parsets = [];
      $scope.years = _.range(project.dataStart, project.dataEnd+1);
      var iLast = $scope.years.length - 1;
      $scope.state = {
        maxtime: '10',
        isRunnable: false,
        parset: undefined,
        startYear: $scope.years[0],
        endYear: $scope.years[iLast]
      };

      console.log("project", project);

      // Check if project has spreadsheet uploaded
      $scope.isMissingData = !project.hasParset;
      if ($scope.isMissingData) {
        return;
      }

      // Fetching list of parsets for open project
      $http
        .get('/api/project/' + project.id + '/parsets')
        .success(function(response) {
          var parsets = response.parsets;
          console.log('parsets', parsets);
          if (parsets) {
            $scope.parsets = parsets;
            $scope.state.parset = getMostRecentItem(parsets, 'updated');
            $scope.setActiveParset();
          }
        });
    }

    function getMostRecentItem(aList, datetimeProp) {
      var aListByDate = _.sortBy(aList, function(item) {
        return new Date(item[datetimeProp]);
      });
      var iLast = aListByDate.length - 1;
      return aListByDate[iLast];
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

    function loadParametersAndGraphs(response) {
      console.log("loaded response", response);
      $scope.graphs = response.graphs;
      $scope.parameters = angular.copy(response.parameters);
    }

    function fetchParameters() {
      return $scope.parameters;
    }

    $scope.getCalibrationGraphs = function() {
      console.log('active parset id', $scope.state.parset.id);
      $http
        .post(
          '/api/project/' + project.id
          + '/parsets/' + $scope.state.parset.id
          + '/calibration',
          {
            which: getSelectors(),
          })
        .success(function(response) {
          loadParametersAndGraphs(response);
          toastr.success('Loaded graphs');
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
      $http
        .post(
          '/api/project/' + project.id
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

    $scope.addParameterSet = function() {
      function add(name) {
        $http
          .post(
            '/api/project/' + project.id + '/parsets',
            {name: name})
          .success(function(response) {
            $scope.parsets = response;
            $scope.state.parset = response[response.length - 1];
            toastr.success('Created parset');
            $scope.setActiveParset();
          });
      }

      renameModalService.openEditNameModal(
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
              '/api/project/' + project.id + '/parsets',
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
        renameModalService.openEditNameModal(
          copy, 'Copy parameter set', 'Enter name',
          renameModalService.getUniqueName(name, names),
          'Name already exists',
          names);
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
            '/api/project/' + project.id
            + '/parsets/' + $scope.state.parset.id,
            {name: name})
          .success(function() {
            $scope.state.parset.name = name;
            toastr.success('Copied parset');
          });
      }

      renameModalService.openEditNameModal(
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
            '/api/project/' + project.id
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
          '/api/project/' + project.id
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
            url: '/api/project/' + project.id
            + '/parsets/' + $scope.state.parset.id
            + '/data',
            file: event.target.files[0]
          }).success(function(response) {
            loadParametersAndGraphs(response);
            $scope.setActiveParset()
          });
        }).click();
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
            '/api/project/' + project.id
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
          '/api/project/' + project.id
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
        '/api/project/' + project.id
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
