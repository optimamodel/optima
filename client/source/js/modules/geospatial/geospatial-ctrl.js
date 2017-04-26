define(
  ['./module', 'angular', 'underscore'], function(module, angular, _) {

    'use strict';

    module.controller(
      'PortfolioController',
      function($scope, modalService, userManager, utilService,
               $state, toastr, projectService, pollerService) {

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

          $scope.portfolios = [];
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
          }
          console.log('loadPortfolios portfolio', $scope.state.portfolio)
        }

        $scope.chooseNewPortfolio = function() {
          $scope.state.objectives = $scope.state.portfolio.objectives;
          utilService
            .rpcAsyncRun(
              'check_task', [$scope.state.portfolio.id, 'portfolio'])
            .then(function(response) {
              console.log('chooseNewPortfolio ga status:', response.data.status);
              if (response.data.status === 'started') {
                initFullGaPoll();
              }
            });
          _.each($scope.state.portfolio.projects, function(project) {
            $scope.bocStatusMessage[project.id] = project.boc;
            utilService
              .rpcAsyncRun(
                'check_task', [project.id, 'boc'])
              .then(function(response) {
                console.log('chooseNewPortfolio project', project.id, 'status:', response.data.status);
                if (response.data.status === 'started') {
                  initProjectBocPoll(project.id);
                }
              });
          });
        };

        $scope.createPortfolio = function() {
          modalService.rename(
            function(name) {
              utilService
                .rpcRun(
                  'create_portfolio', [name])
                .then(function(response) {
                  var data = response.data;
                  console.log('createPortfolio', data);
                  $scope.portfolios.push(data);
                  $scope.state.portfolio = data;
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

        $scope.renamePortfolio = function() {
          modalService.rename(function(newName) {
            utilService
              .rpcRun(
                'rename_portfolio', [$scope.state.portfolio.id, newName])
              .then(function(response) {
                console.log('renamed portfolio', response.data);
                var renamedPortfolio = response.data;
                var portfolio = _.findWhere($scope.portfolios, {id: $scope.state.portfolio.id});
                portfolio.name = newName;
                $scope.state.portfolio.name = newName;
                toastr.success('Renamed portfolio');
              });
            },
            'Rename portfolio',
            'Enter portfolio name',
            $scope.state.portfolio.name,
            'Name already exists',
            _.without(_.pluck($scope.portfolios, 'name'), $scope.state.portfolio.name));
        };

        $scope.downloadPortfolio = function() {
          utilService
            .rpcDownload(
              'download_portfolio', [$scope.state.portfolio.id])
            .then(function(response) {
              toastr.success('Downloaded portfolio');
            });

        };

        $scope.uploadPortfolio = function() {
          utilService
            .rpcUpload('update_portfolio_from_prt')
            .then(function(response) {
              console.log('uploadPortfolio response.data', response.data);
              $scope.portfolios.push(response.data);
              $scope.state.portfolio = response.data;
              loadPortfolios($scope.portfolios);
              toastr.success('Uploaded portfolio');
            });
        };

        $scope.deletePortfolio = function() {
          utilService
            .rpcRun('delete_portfolio', [$scope.state.portfolio.id])
            .then(function(response) {
              console.log('deletePortfolio', response);
              toastr.success('Deleted portfolio');
              loadPortfolios(response.data.portfolios);
            });
        };

        function reloadPortfolio() {
          $scope.bocStatusMessage = {};
          pollerService.stopPolls();
          utilService
            .rpcRun('load_portfolio_summaries')
            .then(function(response) {
              loadPortfolios(response.data.portfolios);
            });
        }

        $scope.calculateAllBocCurves = function() {
          console.log('calculateAllBocCurves', $scope.state.portfolio);
          utilService
            .rpcAsyncRun(
              'launch_boc', [$scope.state.portfolio.id, $scope.state.bocMaxtime])
            .then(function(response) {
              _.each($scope.state.portfolio.projects, function(project) {
                initProjectBocPoll(project.id);
              });
            });
        };

        $scope.deleteProject = function(projectId) {
          utilService
            .rpcRun(
              'delete_portfolio_project',
              [$scope.state.portfolio.id, projectId])
            .then(function(response) {
              toastr.success('Deleted project in portfolio');
              loadPortfolios(response.data.portfolios);
            });
        };

        $scope.runFullGa = function() {
          utilService
            .rpcAsyncRun(
              'check_task', [$scope.state.portfolio.id, 'portfolio'])
            .then(function(response) {
              if (response.data.status != 'started') {
                console.log('runFullGa');
                utilService
                  .rpcAsyncRun(
                    'launch_miminize_portfolio',
                    [$scope.state.portfolio.id, $scope.state.maxtime])
                  .then(function(response) {
                    initFullGaPoll();
                  });
              }
            });
        };

        function initProjectBocPoll(projectId) {
          console.log('initProjectBocPoll', projectId);
          pollerService
            .startPollForRpc(
              projectId,
              'boc',
              function(response) {
                var calcState = response.data;
                if (calcState.status === 'completed') {
                  $scope.bocStatusMessage[projectId] = "calculated";
                  reloadPortfolio();
                  toastr.success('Budget-objective curves calculated');
                } else if (calcState.status === 'started') {
                  var start = new Date(calcState.start_time);
                  var now = new Date(calcState.current_time);
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
          pollerService
            .startPollForRpc(
              $scope.state.portfolio.id,
              'portfolio',
              function(response) {
                var calcState = response.data;
                if (calcState.status === 'completed') {
                  $scope.statusMessage = "";
                  reloadPortfolio();
                  toastr.success('Geospatial optimization completed');
                } else if (calcState.status === 'started') {
                  var start = new Date(calcState.start_time);
                  var now = new Date(calcState.current_time);
                  var diff = now.getTime() - start.getTime();
                  var seconds = parseInt(diff / 1000);
                  $scope.statusMessage = "Optimization running for " + seconds + " s";
                } else {
                  $scope.statusMessage = 'Optimization failed';
                  $scope.state.portfolio.isRunnable = true;
                }
              })
        }

        $scope.savePortfolio = function() {
          utilService
            .rpcRun(
              'save_portfolio_by_summary',
              [$scope.state.portfolio.id, $scope.state.portfolio])
            .then(function(response) {
              toastr.success('Portfolio saved');
              loadPortfolios(response.data.portfolios);
            });
        };

        $scope.addProject = function() {
          $scope.isSelectNewProject = true;
          utilService
            .rpcRun(
              'load_current_user_project_summaries', [userManager.user.id])
            .then(function(response) {
              var selectedIds = _.pluck($scope.state.portfolio.projects, "id");
              $scope.projects = [];
              _.each(response.data.projects, function(project) {
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
          projectService
            .getProjectList()
            .then(function(response) {
              var selectedIds = [];
              if ($scope.state.portfolio) {
                selectedIds = _.pluck($scope.state.portfolio.projects, "id");
              }
              $scope.projects = [];
              _.each(response.data.projects, function(project) {
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
          utilService
            .rpcDownload(
                'make_region_template_spreadsheet',
                [
                  $scope.state.templateProject.id,
                  $scope.state.nRegion,
                  $scope.state.templateYear
                ]
            );
        };

        $scope.spawnRegionsFromSpreadsheet = function() {
          utilService
            .rpcUpload(
              'make_region_projects', [$scope.state.templateProject.id])
            .then(function(response) {
              $scope.state.prjNames = response.data.prjNames;
              console.log('$scope.state.prjNames', $scope.state.prjNames);
              _.each(prjNames, function(prjName) {
                toastr.success('Project created: ' + prjName);
              });

            });
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
          utilService
            .rpcDownload(
              'export_portfolio', [$scope.state.portfolio.id]);
        };

        initialize();

      }
    );

  });
