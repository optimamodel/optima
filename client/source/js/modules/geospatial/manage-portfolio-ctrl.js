define(
  ['./module', 'angular', 'underscore'], function(module, angular, _) {

    'use strict';

    module.controller(
      'PortfolioController',
      function($scope, $http, activeProject, modalService, userManager,
               $state, toastr, globalPoller, $modal, $upload) {

        function initialize() {

          $scope.objectiveKeyLabels = [
            {'key': 'start', 'label': 'Start year'},
            {'key': 'end', 'label': 'End year'},
            {'key': 'budget', 'label': 'Budget'},
            {'key': 'deathweight', 'label': 'Death weight'},
            {'key': 'inciweight', 'label': 'Incidence weight'},
          ];

          $scope.isSelectNewProject = false;
          $scope.isSelectTemplateProject = false;
          $scope.state = {
            portfolio: undefined,
            nRegion: 2,
            objectives: undefined,
            tempateProject: null
          };

          reloadPortfolio();
        }

        function loadPortfolios(portfolios) {
          console.log('loadPortfolios', portfolios)
          var currentPortfolioId = null;
          if (!_.isUndefined($scope.state.portfolio)) {
            currentPortfolioId = $scope.state.portfolio.id;
          }
          $scope.portfolios = portfolios;
          $scope.state.portfolio = undefined;
          if ($scope.portfolios.length > 0) {
            $scope.state.portfolio = _.findWhere($scope.portfolios, {id: currentPortfolioId});
            if (!$scope.state.portfolio) {
              $scope.state.portfolio = $scope.portfolios[0];
            }
            $scope.chooseNewPortfolio();
          };
          console.log('loadPortfolios portfolio', $scope.state.portfolio)
        }

        $scope.chooseNewPortfolio = function() {
          $scope.state.objectives = $scope.state.portfolio.objectives;
          $http
            .get(getCheckFullGaUrl())
            .success(function(response) {
              console.log('chooseNewPortfolio ga status:', response.status);
              if (response.status === 'started') {
                initFullGaPoll();
              }
            });
          _.each($scope.state.portfolio.projects, function(project) {
            $scope.bocStatusMessage[project.id] = project.boc;
            $http
              .get(getCheckProjectBocUrl(project.id))
              .success(function(response) {
                console.log('chooseNewPortfolio project', project.id, 'status:', response.status);
                if (response.status === 'started') {
                  initProjectBocPoll(project.id);
                }
              });
          });
        };

        $scope.createPortfolio = function() {
          modalService.rename(
            function(name) {
              $http
                .post(
                  '/api/portfolio', {name: name})
                .success(function(response) {
                  console.log('created portfolio', response);
                  $scope.portfolios.push(response);
                  $scope.state.portfolio = response;
                  loadPortfolios($scope.portfolios);
                  toastr.success('Created portfolio');
                });
            },
            'Create portfolio',
            'Enter portfolio name',
            '',
            'Name already exists',
            _.pluck($scope.portfolios, 'name'));
        };


        $scope.downloadPortfolio = function() {
          $http.get('/api/portfolio/' + $scope.state.portfolio.id + '/data',
            {headers: {'Content-type': 'application/octet-stream'}, responseType: 'blob'})
            .success(function(response, status, headers, config) {
              var blob = new Blob([response], {type: 'application/octet-stream'});
              saveAs(blob, ($scope.state.portfolio.name + '.prt'));
            });
        };

        $scope.uploadPortfolio = function() {
          angular
            .element('<input type="file">')
            .change(function(event) {
              var file = event.target.files[0];
              $upload
                .upload({
                  url: '/api/portfolio/' + $scope.state.portfolio.id + '/data',
                  fields: {name: file.name},
                  file: file
                })
                .success(function(response) {
                  console.log('uploaded portfolio', response);
                  $scope.portfolios.push(response);
                  $scope.state.portfolio = response;
                  loadPortfolios($scope.portfolios);
                  toastr.success('Uploaded portfolio');
                });
            })
            .click();
        };

        $scope.deletePortfolio = function() {
          $http
            .delete('/api/portfolio/' + $scope.state.portfolio.id)
            .success(function(portfolios) {
              toastr.success('Deleted portfolio');
              loadPortfolios(portfolios);
            });
        };

        function reloadPortfolio() {
          $scope.bocStatusMessage = {};
          globalPoller.stopPolls();
          $http
            .get('/api/portfolio')
            .success(loadPortfolios);
        }

        function getCheckFullGaUrl() {
          return "/api/task/" + $scope.state.portfolio.id
            + "/type/portfolio";
        }

        function getCheckProjectBocUrl(projectId) {
          return "/api/task/" + projectId
            + "/type/boc";
        }

        $scope.calculateAllBocCurves = function() {
          console.log('calculateAllBocCurves', $scope.state.portfolio);
          $http
            .post(
              "/api/portfolio/" + $scope.state.portfolio.id + "/calculate",
              {maxtime: $scope.state.bocMaxtime})
            .success(function() {
              _.each($scope.state.portfolio.projects, function(project) {
                initProjectBocPoll(project.id);
              });
            });
        };

        $scope.deleteProject = function(projectId) {
          $http
            .delete(
              '/api/portfolio/' + $scope.state.portfolio.id
              + '/project/' + projectId)
            .success(function(portfolios) {
              toastr.success('Deleted project in portfolio');
              loadPortfolios(portfolios);
            });
        };

        $scope.runFullGa = function() {
          $http
            .get(getCheckFullGaUrl())
            .success(function(response) {
              console.log('start job response', response);
              if (response.status != 'started') {
                $http
                  .post(
                    "/api/portfolio/" + $scope.state.portfolio.id + "/minimize",
                    {maxtime: $scope.state.maxtime})
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
                $scope.state.portfolio.isRunnable = true;
              }
            }
          );
        }

        function initFullGaPoll() {
          globalPoller.startPoll(
            $scope.state.portfolio.id,
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
                $scope.state.portfolio.isRunnable = true;
              }
            }
          );
        }

        $scope.savePortfolio = function() {
          console.log('Saving portfolio', $scope.state.portfolio);
          $http
            .post(
              "/api/portfolio/" + $scope.state.portfolio.id,
              angular.copy($scope.state.portfolio))
            .success(function(response) {
              toastr.success('Portfolio saved');
              loadPortfolios(response);
            });
        };

        $scope.addProject = function() {
          $scope.isSelectNewProject = true;
          $http
            .get('/api/project')
            .success(function(response) {
              var selectedIds = _.pluck($scope.state.portfolio.projects, "id");
              $scope.projects = [];
              _.each(response.projects, function(project) {
                var isSelected = _.contains(selectedIds, project.id);
                if (project.isOptimizable) {
                  $scope.projects.push({
                    'name': project.name,
                    'id': project.id,
                    'selected': isSelected
                  })
                }
              });
              console.log("$scope.projects", $scope.projects);
            });
        };

        $scope.dismissAddProject = function() {
          $scope.isSelectNewProject = false;
        };

        $scope.saveSelectedProject = function() {
          $scope.isSelectNewProject = false;
          var selectedIds = _.pluck($scope.state.portfolio.projects, "id");
          console.log("selectedIds", selectedIds);
          console.log("$scope.projects", $scope.projects);
          _.each($scope.projects, function(project) {
            if (!_.contains(selectedIds, project.id)) {
              if (project.selected) {
                console.log('new project', project.name);
                $scope.state.portfolio.projects.push({
                  "id": project.id,
                  "name": project.name,
                  "boc": "none"
                });
              }
            }
          });

          $scope.savePortfolio();
        };

        $scope.chooseTemplateProject = function() {
          $scope.isSelectTemplateProject = true;
          $http
            .get('/api/project')
            .success(function(response) {
              var selectedIds = [];
              if ($scope.state.portfolio) {
                selectedIds = _.pluck($scope.state.portfolio.projects, "id");
              }
              $scope.projects = [];
              _.each(response.projects, function(project) {
                var isSelected = _.contains(selectedIds, project.id);
                if (project.isOptimizable) {
                  var project = angular.copy(project);
                  _.extend(project, {
                    'name': project.name,
                    'id': project.id,
                    'selected': isSelected
                  });
                  $scope.projects.push(project)
                }
              });
              console.log("$scope.projects", $scope.projects);
            });
        };

        $scope.dismissSelectTemplateProject = function() {
          $scope.isSelectTemplateProject = false;
        };

        $scope.saveTemplateProject = function() {
          $scope.isSelectTemplateProject = false;
          var project = $scope.state.templateProject;
          $scope.years = _.range(project.startYear, project.endYear + 1);
          $scope.state.templateYear = $scope.years[0];
          console.log('template project', $scope.state.templateProject);
          console.log('years', $scope.years);
        };

        $scope.generateTemplateSpreadsheet = function() {
          $http
            .post(
              '/api/region',
              {
                projectId: $scope.state.templateProject.id,
                nRegion: $scope.state.nRegion,
                year: $scope.state.templateYear
              },
              {
                responseType: "arraybuffer"
              })
            .success(function(data) {
              var blob = new Blob(
                [data],
                {
                  type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                });
              saveAs(blob, 'geospatial-subdivision.xlsx');
            });
        };

        $scope.spawnRegionsFromSpreadsheet = function() {
          // upload file then create projects
          // then add to portfolio
          angular
            .element('<input type="file">')
            .change(function(event) {
              $upload
                .upload({
                  url: '/api/spawnregion',
                  fields: {projectId: $scope.state.templateProject.id},
                  file: event.target.files[0]
                })
                .success(function(prjNames) {
                  $scope.state.prjNames = prjNames;
                  console.log('$scope.state.prjNames', $scope.state.prjNames);
                  _.each(prjNames, function(prjName) {
                    toastr.success('Project created: ' + prjName);
                  });
                });

            })
            .click();
        };

        $scope.checkBocCurvesNotCalculated = function() {
          if (_.isUndefined($scope.state.portfolio)) {
            return true;
          }
          var allCalculated = true;
          _.each($scope.state.portfolio.projects, function(project) {
            if ($scope.bocStatusMessage[project.id] !== "calculated") {
              allCalculated = false;
            }
          });
          return !allCalculated;
        };

        $scope.exportResults = function() {
          $http.get('/api/portfolio/' + $scope.state.portfolio.id + '/export',
            {headers: {'Content-type': 'application/octet-stream'}, responseType: 'blob'})
            .success(function(response, status, headers, config) {
              var blob = new Blob([response], {type: 'application/octet-stream'});
              saveAs(blob, ('geospatial-results.xlsx'));
            });
        };

        initialize();

      }
    );

});
