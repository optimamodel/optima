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

          $scope.isSelectNewProject = false;

          reloadPortfolio();
        }

        function reloadPortfolio() {
          $scope.bocStatusMessage = {};
          globalPoller.stopPolls();
          $http
            .get('/api/portfolio')
            .success(function(response) {
              console.log('load portfolio', response);
              $scope.state = response;
              $scope.activeGaoptim = $scope.state.gaoptims[0];
              $http
                .get(getCheckFullGaUrl())
                .success(function(response) {
                  if (response.status === 'started') {
                    initFullGaPoll();
                  }
                });
              _.each($scope.state.projects, function(project) {
                $scope.bocStatusMessage[project.id] = project.boc;
                $http
                  .get(getCheckProjectBocUrl(project.id))
                  .success(function(response) {
                    if (response.status === 'started') {
                      initProjectBocPoll(project.id);
                    }
                  });
              });
            });
        }

        function getCheckFullGaUrl() {
          return "/api/task/" + $scope.state.id
              + "/type/portfolio-" + $scope.activeGaoptim.id;
        }

        function getCheckProjectBocUrl(projectId) {
          return "/api/task/" + projectId
                + "/type/gaoptim-" + $scope.activeGaoptim.id;
        }

        $scope.calculateAllBocCurves = function() {
          console.log('run BOC curves', $scope.state);
          $http
            .get(
              "/api/portfolio/" + $scope.state.id
              + "/gaoptim/" + $scope.activeGaoptim.id)
            .success(function() {
              _.each($scope.state.projects, function(project) {
                initProjectBocPoll(project.id);
              });
            });
        };

        $scope.deleteProject = function(projectId) {
          $http
            .delete(
              '/api/portfolio/' + $scope.state.id
                + '/project/' + projectId)
            .success(function() {

            });
        };

        $scope.runFullGa = function() {
          $http
            .get(getCheckFullGaUrl())
            .success(function(response) {
              console.log('start job response', response);
              if (response.status != 'started') {
                $http
                  .get(
                    "/api/minimize/portfolio/" + $scope.state.id
                    + "/gaoptim/" + $scope.activeGaoptim.id)
                  .success(function() {
                    initFullGaPoll();
                  });
              }
            });
        };

        function initProjectBocPoll(projectId) {
          globalPoller.startPoll(
            projectId,
            getCheckProjectBocUrl(projectId),
            function(response) {
              if (response.status === 'completed') {
                $scope.bocStatusMessage[projectId] = "calculated";
                reloadPortfolio();
                toastr.success('BOC calculation finished');
              } else if (response.status === 'started') {
                var start = new Date(response.start_time);
                var now = new Date(response.current_time);
                var diff = now.getTime() - start.getTime();
                var seconds = parseInt(diff / 1000);
                $scope.bocStatusMessage[projectId] = "running for " + seconds + " s";
              } else {
                $scope.bocStatusMessage[projectId] = 'failed';
                $scope.state.isRunnable = true;
              }
            }
          );
        }

        function initFullGaPoll() {
          globalPoller.startPoll(
            $scope.activeGaoptim.id,
            getCheckFullGaUrl(),
            function(response) {
              if (response.status === 'completed') {
                $scope.statusMessage = "";
                reloadPortfolio();
                toastr.success('GA Optimization completed');
              } else if (response.status === 'started') {
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
          $scope.isSelectNewProject = true;
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

        $scope.dismissAddProject = function() {
          $scope.isSelectNewProject = false;
        };

        $scope.saveSelectedProject = function() {
          $scope.isSelectNewProject = false;
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
                  "boc": "none"
                });
              }
            }
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
        };

        initialize();

      }
    );

  }
);
