define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ModelCalibrationController', function (
      $scope, $http, info, modalService, $upload,
      $modal, $timeout, toastr) {

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    var project = info.data;

    function initialize() {

      $scope.parsets = [];
      $scope.state = {
        maxtime: '10',
        parset: undefined
      };

      // Check if project has spreadsheet uploaded
      if (!project.hasData) {
        modalService.inform(
            function() {
            },
            'Okay',
            'Please upload spreadsheet to proceed.',
            'Cannot proceed'
        );
        $scope.missingData = true;
        return;
      }

      // Fetching list of parsets for open project
      $http
        .get('/api/project/' + project.id + '/parsets')
        .success(function(response) {
          var parsets = response.parsets;
          if (parsets) {
            $scope.parsets = parsets;
            $scope.state.parset = parsets[0];
            initPollAutoCalibration();
            $scope.getGraphs();
          }
        });
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
      console.log(response);
      $scope.graphs = response.graphs;
      $scope.parameters = angular.copy(response.parameters);
    }

    function fetchParameters() {
      return $scope.parameters;
    }

    $scope.getGraphs = function() {
      $http
        .get(
          '/api/project/' + project.id
            + '/parsets/' + $scope.state.parset.id
            + '/calibration',
          {which: getSelectors()})
        .success(function (response) {
          loadParametersAndGraphs(response);
          toastr.success('Loaded graphs');
        });
    };

    $scope.saveAndUpdateGraphs = function() {
      if(!$scope.parameters) {
        return;
      }
      $http
        .post(
          '/api/project/' + project.id
            + '/parsets/' + $scope.state.parset.id
            + '/calibration?doSave=true',
          {
            parameters: fetchParameters(),
            which: getSelectors()
          })
        .success(function (response) {
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
            $scope.getGraphs();
          });
      }
      openParameterSetModal(
        add, 'Add parameter set', $scope.parsets, null, 'Add');
    };

    $scope.copyParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
      } else {
        function rename(name) {
          $http
            .post(
              '/api/project/' + project.id + '/parsets',
              {
                name: name,
                parset_id: $scope.state.parset.id
              })
            .success(function (response) {
              $scope.parsets = response;
              $scope.state.parset = response[response.length - 1];
              toastr.success('Copied parset');
            });
        }
        openParameterSetModal(
          rename, 'Copy parameter set', $scope.parsets,
          $scope.state.parset.name + ' copy', 'Copy');
      }
    };

    $scope.renameParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
      } else {
        function rename(name) {
          $http
            .put(
                '/api/project/' + project.id
                  + '/parsets/' + $scope.state.parset.id,
                { name: name})
            .success(function () {
              $scope.state.parset.name = name;
              toastr.success('Copied parset');
            });
        }
        openParameterSetModal(
          rename, 'Rename parameter set', $scope.parsets,
          $scope.state.parset.name, 'Rename', true);
      }
    };

    $scope.deleteParameterSet = function() {
      if (!$scope.state.parset) {
        modalService.informError(
          [{message: 'No parameter set selected.'}]);
      } else {
        function remove() {
          $http
            .delete(
              '/api/project/' + project.id
              + '/parsets/' + $scope.state.parset.id)
            .success(function() {
              $scope.parsets = _.filter(
                $scope.parsets, function (parset) {
                  return parset.id !== $scope.state.parset.id;
                }
              );
              if($scope.parsets.length > 0) {
                $scope.state.parset = $scope.parsets[0];
                toastr.success('Deleted parset');
                $scope.getGraphs();
              }
            });
        }
        // This has been temporarily commented out: https://trello.com/c/omuvJSYD/853-reuploading-spreadsheets-fails-in-several-ways
        // if ($scope.state.parset.name === "default") {
        if ( false ) {
          modalService.informError(
            [{message: 'Deleting the default parameter set is not permitted.'}]);
        } else {
          modalService.confirm(
            remove,
            function () {},
            'Yes, remove this parameter set',
            'No',
            'Are you sure you want to permanently remove parameter set "'
              + $scope.state.parset.name + '"?',
            'Delete parameter set'
          );
        }
      }
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
        .success(function (response) {
          var blob = new Blob(
            [response], {type: 'application/octet-stream'});
          saveAs(blob, ($scope.state.parset.name + '.par.json'));
        });
    };

    $scope.uploadParameterSet = function() {
      angular
        .element('<input type=\'file\'>')
        .change(function(event){
          $upload.upload({
            url: '/api/project/' + project.id
                   + '/parsets/' + $scope.state.parset.id
                   + '/data',
            file: event.target.files[0]
          }).success(function(response) {
            loadParametersAndGraphs(response);
            $scope.getGraphs()
          });
        }).click();
    };

    function openParameterSetModal(
      callback, title, parameterSetList, parameterSetName,
      operation, isRename) {

      var onModalKeyDown = function (event) {
        if(event.keyCode == 27) { return modalInstance.dismiss('ESC'); }
      };
      var modalInstance = $modal.open({
        templateUrl: 'js/modules/model/parameter-set-modal.html',
        controller: ['$scope', '$document', function ($scope, $document) {
          $scope.title = title;
          $scope.name = parameterSetName;
          $scope.operation = operation;
          $scope.updateParameterSet = function () {
            $scope.newParameterSetName = $scope.name;
            callback($scope.name);
            modalInstance.close();
          };
          $scope.isUniqueName = function (parameterSetForm) {
            function isSameName(item) { return item.name == $scope.name; }
            var exists = _(parameterSetList).some(isSameName)
                  && $scope.name !== parameterSetName
                  && $scope.name !== $scope.newParameterSetName;
            if (isRename) {
              parameterSetForm.parameterSetName.$setValidity(
                "parameterSetUpdated", $scope.name !== parameterSetName);
            }
            parameterSetForm.parameterSetName.$setValidity(
              "parameterSetExists", !exists);
            return exists;
          };
          $document.on('keydown', onModalKeyDown); // observe
          $scope.$on(
            '$destroy',
            function () { $document.off('keydown', onModalKeyDown); });  // unobserve
        }]
      });
      return modalInstance;
    }

    $scope.startAutoCalibration = function() {
      var data = {};
      if ($scope.state.maxtime) {
        data.maxtime = Number($scope.state.maxtime);
      }
      $http
        .post(
          '/api/project/' + project.id
          +  '/parsets/' + $scope.state.parset.id
          + '/automatic_calibration',
          data)
        .success(function(response) {
          if(response.status === 'started') {
            $scope.statusMessage = 'Autofit started.';
            $scope.secondsRun = 0;
            $scope.setMaxtime = data.maxtime;
            pollAutoCalibration();
          } else if(response.status === 'blocked') {
            $scope.statusMessage = 'Another calculation on this project is already running.'
          }
        })
    };

    function initPollAutoCalibration() {
      $http
        .get(
          '/api/project/' + project.id
          +  '/parsets/' + $scope.state.parset.id
          + '/automatic_calibration')
        .success(function(response) {
          if (response.status === 'started') {
            pollAutoCalibration();
          }
        });
    }

    function pollAutoCalibration() {
      $http
        .get(
          '/api/project/' + project.id
            + '/parsets/' + $scope.state.parset.id
            + '/automatic_calibration')
        .success(function(response) {
          if (response.status === 'completed') {
            $scope.getAutoCalibratedGraphs();
            $scope.statusMessage = '';
            toastr.success('Autofit completed');
            $timeout.cancel($scope.pollTimer);
          } else if (response.status === 'error') {
            $scope.statusMessage = 'Error in running autofit.';
            $timeout.cancel($scope.pollTimer);
          } else if (response.status === 'started') {
            var start = new Date(response.start_time);
            var now = new Date();
            var diff = now.getTime() - start.getTime();
            var seconds = diff / 1000;
            $scope.statusMessage = "Autofit running for " + parseInt(seconds) + " s";
            $scope.pollTimer = $timeout(pollAutoCalibration, 1000);
          }
        });
    }

    $scope.getAutoCalibratedGraphs = function() {
      $http
        .post(
          '/api/project/' + project.id
            + '/parsets' + '/' + $scope.state.parset.id
            + '/calibration',
          {which: getSelectors()})
        .success(function(response) {
          toastr.success('Graphs uploaded');
          loadParametersAndGraphs(response);
        });
    };

    initialize();

  });
});
