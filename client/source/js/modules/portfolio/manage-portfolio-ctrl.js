define(
  ['./module', 'angular', 'underscore'], function (module, angular, _) {

    'use strict';

    module.controller(
      'PortfolioController',
      function (
        $scope, $http, activeProject, modalService, fileUpload,
        UserManager, $state, toastr, globalPoller) {

        function initialize() {

          $scope.objectiveKeyLabels = [
            {'key': 'start', 'label':'Start year' },
            {'key': 'end', 'label': 'End year'},
            {'key': 'budget', 'label': 'Budget'},
            {'key': 'deathweight', 'label': 'Death weight'},
            {'key': 'inciweight', 'label': 'Incidence weight'},
          ];

          reloadPortfolio();
          $scope.isSelectProject = false;
        }

        function reloadPortfolio() {
          globalPoller.stopPolls();

          $http
            .get('/api/portfolio')
            .success(function(response) {
              console.log('load portfolio', response)
              $scope.state = response;
              $scope.activeGaoptim = $scope.state.gaoptims[0];
              $http
                .get(getCheckFullGAUrl())
                .success(function(response) {
                  if (response.status === 'started') {
                    initGaPoll();
                  }
                })
            });

        }

        function getCheckFullGAUrl() {
          return "/api/task/" + $scope.state.id
              + "/type/portfolio-" + $scope.activeGaoptim.id;
        }

        $scope.runGeospatial = function() {
          console.log('run', $scope.state);
          $http
            .get(
              "/api/portfolio/" + $scope.state.id
              + "/gaoptim/" + $scope.activeGaoptim.id)
            .success(function(response) {
              console.log(response);
            });
        };

        $scope.runMinOutcome = function() {
          var url = "/api/task/" + $scope.state.id
              + "/type/portfolio-" + $scope.activeGaoptim.id;
          $http
            .get(url)
            .success(function(response) {
              console.log('start job response', response);
              if (response.status != 'started') {
                $http
                  .get(
                    "/api/minimize/portfolio/" + $scope.state.id
                    + "/gaoptim/" + $scope.activeGaoptim.id)
                  .success(function(response) {
                    console.log(response);
                    console.log('Start fullGA poll');
                    initGaPoll();
                  });

              } else {
              }
            });
        };

        $scope.killBocs = function() {
          _.each($scope.state.projects, function(project) {
            var url = "/api/task/" + project.id
                + "/type/gaoptim-" + $scope.activeGaoptim.id;
            console.log('kill job' + url);
            $http
              .delete(url)
              .success(function(response) {
                toastr.success(response);
              });

          });
        };

        function initBocPoll(projectId) {
          globalPoller.startPoll(
            projectId,
            getCheckFullGAUrl(),
            function(response) {
              if (response.status === 'completed') {
                $scope.statusMessage = "";
                reloadPortfolio();
                toastr.success('GA Optimization completed');
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


        function initGaPoll() {
          globalPoller.startPoll(
            $scope.activeGaoptim.id,
            getCheckFullGAUrl(),
            function(response) {
              if (response.status === 'completed') {
                $scope.statusMessage = "";
                reloadPortfolio();
                toastr.success('GA Optimization completed');
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

        $scope.killMinOutcome = function() {
          var url = "/api/task/" + $scope.state.id
              + "/type/portfolio-" + $scope.activeGaoptim.id;
          console.log('kill job' + url);
          $http
            .delete(url)
            .success(function(response) {
              toastr.success(response);
            });
        };

        $scope.savePortfolio = function() {
          $http
            .post(
              "/api/portfolio/" + $scope.state.id,
              angular.copy($scope.state))
            .success(function(response) {
              console.log(response);
              toastr.success('saved objectives')
            });
        };

        $scope.addProject = function() {
          $scope.isSelectProject = true;
          $http
            .get('/api/project')
            .success(function(response) {
              var selectedIds = _.pluck($scope.state.projects, "id");
              $scope.projects = [];
              _.each(response.projects, function(project) {
                var isSelected = _.contains(selectedIds, project.id);
                $scope.projects.push({
                  'name': project.name,
                  'id': project.id,
                  'selected': isSelected
                })
              });
              console.log("$scope.projects", $scope.projects);
            });
        };

        $scope.dismissAdd = function() {
          $scope.isSelectProject = false;
        };

        $scope.saveSelectedProject = function() {
          $scope.isSelectProject = false;
          var selectedIds = _.pluck($scope.state.projects, "id");
          console.log("selectedIds", selectedIds);
          console.log("$scope.projects", $scope.projects);
          _.each($scope.projects, function(project) {
            if (!_.contains(selectedIds, project.id)) {
              if (project.selected) {
                console.log('new project', project.name);
                $scope.state.projects.push({
                  "id": project.id,
                  "name": project.name,
                  "boc": "none",
                });
              }
            };
          });

          console.log($scope.state.projects)
          $scope.savePortfolio();
          toastr.success('stop adding')
        };

        $scope.hasNoResults = function() {
          if (_.isUndefined($scope.state)) {
            return true;
          }
          return !($scope.state.outputstring);
        };

        $scope.exportResults = function() {
          if ($scope.state.outputstring) {
            var blob = new Blob(
              [$scope.state.outputstring], {type: 'application/octet-stream'});
            saveAs(blob, ('result.csv'));
          }
        }

        initialize();

      }
    );

  }
);
