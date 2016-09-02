define(
  ['./module', 'angular', 'underscore'],
  function (module, angular, _) {
  'use strict';

    // {
    //   "name": "default",
    //   "created": "Mon, 21 Mar 2016 14:04:54 GMT",
    //   "version": 2,
    //   "gaoptims": [
    //     [
    //       "5f9ac402-1a0c-468c-ae0b-5b598be6a44d",
    //       {
    //         "objectives": {
    //           "which": "outcomes",
    //           "keys": [
    //             "death",
    //             "inci"
    //           ],
    //           "keylabels": {
    //             "inci": "New infections",
    //             "death": "Deaths"
    //           },
    //           "base": null,
    //           "start": 2017,
    //           "end": 2030,
    //           "budget": 17456726.6828,
    //           "deathweight": 5,
    //           "inciweight": 1,
    //           "deathfrac": null,
    //           "incifrac": null
    //         },
    //         "resultpairs": {
    //           "98c15e0f-f9ab-44ea-95cc-9af3a2f9dcad": {
    //             "init": null,
    //             "opt": null
    //           },
    //           "85c2864c-d3c4-4af5-a3ee-7f8d7a55e42b": {
    //             "init": null,
    //             "opt": null
    //           }
    //         },
    //         "id": "5f9ac402-1a0c-468c-ae0b-5b598be6a44d",
    //         "name": "default"
    //       }
    //     ]
    //   ],
    //   "outputstring": "...",
    //   "id": "99e73475-0541-4339-b221-9459855e1783",
    //   "gitversion": "80833b5d9fa0294c3c376a79ea8adc8355cffdb0"
    // }

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

          globalPoller.stopPolls();

          $http
            .get(
              '/api/portfolio')
            .success(function(response) {
              console.log(response);
              $scope.state = response;
              $scope.activeGaoptim = $scope.state.gaoptims[0];

              var url = "/api/task/" + $scope.state.id
                + "/type/portfolio-" + $scope.activeGaoptim.id;
              console.log('check fullGA: ' + url);
              $http
                .get(url)
                .success(function(response) {
                  console.log(response);
                  if (response.status === 'started') {
                    initGaPoll();
                  }
                })

            });

          $scope.isSelectProject = false;
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
          console.log($scope.state);
          console.log($scope.activeGaoptim);
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

        function initGaPoll() {
          globalPoller.startPoll(
            $scope.activeGaoptim.id,
            "/api/task/" + $scope.state.id
              + "/type/portfolio-" + $scope.activeGaoptim.id,
            function(response) {
              if (response.status === 'completed') {
                $scope.statusMessage = 'Loading graphs...';
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
          toastr.success('adding')
        };

        $scope.dismissAdd = function() {
          $scope.isSelectProject = false;
          toastr.success('stop adding')
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

        initialize();

      }
    );

  }
);
