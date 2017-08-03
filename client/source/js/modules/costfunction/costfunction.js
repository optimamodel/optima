define(['angular', 'underscore', 'toastr'], function(angular, _) {


  var module = angular.module('app.cost-functions', ['ui.router', 'toastr']);


  /**
   * The costfunction page is slightly different to the other pages
   * in that it is a tabbed page.
   *
   * From legacy code, the vm approach (instead of $scope) was
   * taken to pass the controller into the page. Originally,
   * each tabbed page was
   * on a different page, so that vm (=this) was used to specify
   * the page controller as opposed to $scope for the individual
   * tabs. Since then, all the tabbed panels have been merged
   * back, and so vm is legacy.
   */


  module.config(function ($stateProvider) {
    $stateProvider
      .state('costfunction', {
        url: '/cost-function',
        controller: 'ModelCostCoverageController as vm',
        templateUrl: 'js/modules/costfunction/cost-function.html?cacheBust=xxx',
        bindToController: true,
      });
  });


  module.controller(
    'ModelCostCoverageController',
    function($scope, toastr, $state, projectService, pollerService, rpcService) {

      var vm = this;

      function initialize() {
        vm.activeTab = 'cost';
        vm.tabs = [
          {
            name: 'Define cost functions',
            slug: 'cost'
          },
          {
            name: 'Define outcome functions',
            slug: 'outcome'
          },
          {
            name: 'Summary',
            slug: 'summary'
          }
        ];

        vm.state = {};
        vm.progsets = [];
        vm.parsets = [];

        vm.state.year = new Date().getFullYear();
        vm.state.maxtime = 10;

        $scope.projectService = projectService;
        $scope.$watch('projectService.project.id', function() {
          if (!_.isUndefined(vm.project) && (vm.project.id !== projectService.project.id)) {
            console.log('ModelCostCoverageController project-change', projectService.project.name);
            reloadActiveProject(false);   // we're not using an Undo stack here 
          }
        });

        // Load the active project, telling the function we're not using an Undo stack.
        reloadActiveProject(false);
      }

      function reloadActiveProject(useUndoStack) {
        projectService
          .getActiveProject()
          .then(function(response) {
            vm.project = response.data;
            console.log('reloadActiveProject init vm.project', vm.project);

            // Initialize a new UndoStack on the server if we are not using an UndoStack in this 
            // call.
            if (!useUndoStack) {
              rpcService
                .rpcRun(
                  'init_new_undo_stack', [vm.project.id]);
            }

            // Fetch progsets
            return rpcService.rpcRun('load_progset_summaries', [vm.project.id]);
          })
          .then(function(response) {
            vm.progsets = response.data.progsets;
            console.log('reloadActiveProject init vm.progsets', vm.progsets);
            vm.state.progset = vm.progsets[0];

            // Fetch parsets
            return rpcService.rpcRun('load_parset_summaries', [vm.project.id]);
          })
          .then(function(response) {
            vm.parsets = response.data.parsets;
            console.log('reloadActiveProject vm.parsets', vm.parsets);
            vm.state.parset = vm.parsets[0];
            vm.changeProgsetAndParset();

            vm.state.yearSelector = _.range(
              vm.project.startYear, vm.project.endYear + 1);

            // Stop here if spreadsheet has not been uploaded
            vm.isMissingData = !vm.project.calibrationOK;
            if (vm.isMissingData) {
              return;
            }

            vm.hasNoProgram = vm.project.nProgram === 0;
            if (vm.hasNoProgram) {
              return;
            }

            if (_.isUndefined(window.loadCostCovGraphResize)) {
              $(window).bind('resize', function() {
                $scope.onResize();
              });
              window.loadCostCovGraphResize = true;
            }
          });
      }

      $scope.onResize = function() {
        function setAllFiguresToWidth($element) {
          $element.find('svg.mpld3-figure').each(function () {
            var $svgFigure = $(this);
            var ratio = $svgFigure.attr('width') / $svgFigure.attr('height');
            var parent = $svgFigure.parent().parent().parent().parent();
            var width = parent.width();
            var height = width / ratio;
            $svgFigure.attr('width', width);
            $svgFigure.attr('height', height);
          });
          $scope.$apply();
        }
        setAllFiguresToWidth($(".costcov-chart-container"));
      };

      function consoleLogJson(name, val) {
        console.log(name + ' = ');
        console.log(JSON.stringify(val, null, 2));
      }

      function changeParset() {
        console.log('changeParset', vm.state.parset);
        if (vm.state.progset && vm.state.parset) {
          rpcService.rpcRun(
            'load_parameters_from_progset_parset',
            [vm.project.id, vm.state.progset.id, vm.state.parset.id])
          .then(function(response) {
            vm.parameters = response.data.parameters;
            console.log('changeParset parameters', vm.parameters);
            vm.state.parameter = vm.parameters[0];
            vm.changeTargetParameter();
          });
        }
      }

      vm.changeProgram = function() {
        rpcService.rpcRun(
          'load_target_popsizes',
          [vm.project.id, vm.state.parset.id, vm.state.progset.id, vm.state.program.id])
        .then(function(response) {
            vm.state.popsizes = response.data;
            console.log('changeProgram popsizes', vm.state.popsizes);
            buildCostFunctionTables();
            vm.updateCostCovGraph();
        });
      };

      function loadReconcileData() {
        rpcService.rpcRun(
          'load_reconcile_summary',
          [vm.project.id, vm.state.progset.id, vm.state.parset.id, vm.state.year])
        .then(function(response) {
          vm.state.summary = response.data;
          console.log('loadReconcileData', response.data);
        });
      }


      vm.changeProgsetAndParset = function() {
        if (vm.state.progset === undefined) {
          return;
        }

        function isActive(program) {
          return program.targetpars
            && program.targetpars.length > 0
            && program.active;
        }

        vm.programs = _.sortBy(
          _.filter(vm.state.progset.programs, isActive),
          'name');
        console.log('changeProgsetAndParset', vm.programs);
        if (vm.programs.length == 0) {
          return;
        }
        vm.state.program = vm.programs[0];
        if (!("attr" in vm.state.program)) {
          vm.state.program.attr = {caption: "", xupperlim: null};
        }
        console.log('changeProgsetAndParset program', vm.state.program);
        vm.state.popsizes = {};

        rpcService.rpcRun(
          'load_reconcile_summary',
          [vm.project.id, vm.state.progset.id, vm.state.parset.id, vm.state.year])
        .then(function(response) {
          vm.state.summary = response.data;
          console.log('changeProgsetAndParset reconcile', response.data);

          // Fetch outcomes for this progset
          return rpcService.rpcRun(
            'load_progset_outcome_summaries', [vm.project.id, vm.state.progset.id]);
        })
        .then(function(response) {
          console.log('changeProgsetAndParset outcomes', response);
          vm.outcomes = response.data.outcomes;
          console.log('changeProgsetAndParset outcomes', vm.outcomes);
          changeParset();
          vm.changeProgram();
        })
      };

      vm.undo = function() {
        rpcService
          .rpcRun(
            'fetch_undo_project',
            [projectService.project.id])
          .then(function(response) {
		    if (response.data.didundo) {
		      reloadActiveProject(true);
              toastr.success('Undo to previous save complete');
            }
          });		
	  }
	
      vm.redo = function() {
        rpcService
          .rpcRun(
            'fetch_redo_project',
            [projectService.project.id])
          .then(function(response) {
		    if (response.data.didredo) {
		      reloadActiveProject(true);
              toastr.success('Redo to next save complete');	
            }	  
          });      		
	  }

      vm.updateCostCovGraph = function() {
        projectService.getActiveProject();
        vm.chartData = {};
        var years = vm.state.program.ccopars.t;
        if (_.isUndefined(years) || years.length == 0) {
          vm.chartData = null;
          return;
        }
        rpcService
          .rpcRun(
            'load_costcov_graph',
            [vm.project.id, vm.state.progset.id, vm.state.program.id,
            vm.state.parset.id, years])
          .then(
            function(response) {
              vm.state.chartData = response.data;
            },
            function() {
              console.log('Failed to load graph for', vm.state.program.short);
            });
      };

      function revertCcoparsTable() {
        var table = vm.state.ccoparsTable;
        var ccopars = {t: [], saturation: [], unitcost: []};
        table.rows.forEach(function(row, iRow) {
          if (iRow != table.iEditRow) {
            ccopars.t.push(row[0]);
            ccopars.saturation.push([row[2] / 100., row[3] / 100.]);
            ccopars.unitcost.push([row[4], row[5]]);
          }
        });
        vm.state.program.ccopars = ccopars;
      }

      vm.checkLowHighValidationForAllCcopars = function() {
        if (_.isUndefined(vm.state.ccoparsTable)) {
          return false;
        }
        var result = false;
        _.each(vm.state.ccoparsTable.rows, function(row) {
          if (row[3] < row[2]) {
            result = true;
          }
          if (row[5] < row[4]) {
            result = true;
          }
        });
        return result;
      };

      vm.checkLimitViolation = function(val, limits) {
        if (val < limits[0]) {
          return true;
        }
        if (val > limits[1]) {
          return true;
        }
        return false;
      };

      vm.saveProgram = function() {
        revertCcoparsTable();
        console.log('saveProgram', vm.state.program);
        rpcService
          .rpcRun(
            'save_program',
            [vm.project.id, vm.state.program.progset_id, vm.state.program])
          .then(function(response) {
            toastr.success('Cost data were saved');
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [vm.project.id]);
            vm.updateCostCovGraph();
            loadReconcileData();
          })
      };

      vm.addCcoparYear = function() {
        var row = [
          2016,
          '',
          null,
          null,
          null,
          null
        ];
        vm.state.ccoparsTable.rows.push(row);
        vm.setEstPopulationForCcopar();
      };

      vm.setEstPopulationForCcopar = function() {
        _.each(vm.state.ccoparsTable.rows, function(row) {
          var year = row[0];
          if (_.isUndefined(year) || _.isUndefined(vm.state.popsizes)) {
            row[1] = "";
          } else {
            var popsize = vm.state.popsizes[year.toString()];
            if (!_.isNumber(popsize)) {
              row[1] = "";
            } else {
              row[1] = parseInt(popsize);
            }
          }
        });
      };

      vm.deleteCccoparYear = function(iRow) {
        vm.state.ccoparsTable.rows.splice(iRow, 1);
      };

      vm.deleteCostCovDataYear = function(iYear) {
        vm.state.program.costcov.splice(iYear, 1);
      };

      vm.addCostCovDataYear = function() {
        vm.state.program.costcov.push({
          year: 2016, cost: null, coverage: null});
      };


      function buildCostFunctionTables() {
        vm.state.ccoparsTable = {rows: []};
        var ccopars = angular.copy(vm.state.program.ccopars);
        var table = vm.state.ccoparsTable;
        if (ccopars && ccopars.t && ccopars.t.length > 0) {
          for (var iYear = 0; iYear < ccopars.t.length; iYear++) {
            table.rows.push([
              ccopars.t[iYear],
              "",
              ccopars.saturation[iYear][0] * 100.,
              ccopars.saturation[iYear][1] * 100.,
              ccopars.unitcost[iYear][0],
              ccopars.unitcost[iYear][1]
            ])
          }
        }
        vm.setEstPopulationForCcopar();
      }

      // OUTCOME FUNCTIONS

      function getFilteredOutcomes(outcomes) {

        function isProgramNotEmpty(program) {
          return (!_.isNull(program.intercept_lower)
            || !_.isNull(program.intercept_lower));
        }

        function isYearNotEmpty(year) {
          return (!_.isNull(year.intercept_lower)
            || !_.isNull(year.intercept_lower)
            || year.programs.length > 0);
        }

        function isOutcomeNotEmpty(outcome) {
          return outcome.years.length > 0;
        }

        var filteredOutcomes = angular.copy(outcomes);
        _.each(filteredOutcomes, function(outcome) {
          _.each(outcome.years, function(year) {
            year.programs = _.filter(year.programs, isProgramNotEmpty);
          });
          outcome.years = _.filter(outcome.years, isYearNotEmpty);
        });
        filteredOutcomes = _.filter(filteredOutcomes, isOutcomeNotEmpty);
        consoleLogJson('filtered outcomes', filteredOutcomes);

        return filteredOutcomes;
      }

      vm.checkLowHighViolation = function(low, high) {
        return high < low;
      };

      vm.checkLowHighValidationForAllOutcomes = function() {
        var result = false;
        _.each(vm.state.targetedOutcomes, function(outcome) {
          _.each(outcome.years, function(yearEntry) {
            if (yearEntry.intercept_lower > yearEntry.intercept_upper) {
              result = true;
              return;
            }
            _.each(yearEntry.programs, function(program) {
              if (program.intercept_lower > program.intercept_upper) {
                result = true;
                return;
              }
            });
          });
        });
        return result;
      };

      vm.saveProgsetOutcomes = function() {
        rpcService
          .rpcRun(
            'save_outcome_summaries',
            [vm.project.id, vm.state.progset.id, getFilteredOutcomes(vm.outcomes)])
          .then(function(response) {
            toastr.success('Outcomes were saved');
            rpcService
              .rpcRun(
                'push_project_to_undo_stack', 
                [vm.project.id]);
            vm.outcomes = response.data.outcomes;
            console.log('vm.saveProgsetoutcomes', vm.outcomes);
            vm.changeTargetParameter();
            loadReconcileData();
          });
      };

      vm.selectTab = function(tab) {
        vm.activeTab = tab;
        if (tab == "summary") {
          vm.selectSummary();
        }
      };

      vm.makePopKeyLabel = function(popKey) {
        if (typeof popKey === 'string') {
          if (popKey == "tot") {
            return "Total Population";
          }
          return popKey;
        }
        return popKey.join(' <-> ');
      };

      function makePopulationLabel(population) {
        var popKey = population.pop;
        return typeof popKey === 'string' ? popKey : popKey.join(' <-> ');
      }

      vm.getProgramName = function(short) {
        var selector = _.findWhere(vm.programSelector, {value: short});
        return selector.label;
      };

      function addIncompletePops() {

        var existingPops = [];
        _.each(vm.outcomes, function(outcome) {
          if (outcome.name == vm.state.parameter.short) {
            existingPops.push(outcome.pop);
          }
        });

        var missingPops = [];
        _.each(vm.state.parameter.populations, function(population) {
          var findPop = _.find(existingPops, function(pop) {
            return "" + pop == "" + population.pop
          });
          if (!findPop) {
            missingPops.push(population.pop);
          }
        });

        _.each(missingPops, function(pop) {
          vm.outcomes.push({
            name: vm.state.parameter.short,
            pop: pop,
            interact: "random",
            years: []
          })
        });
      }

      function addMissingYear() {
        _.each(vm.outcomes, function(outcome) {
          var years = outcome.years;
          if (years.length == 0) {
            years.push({
              intercept_lower: null,
              intercept_upper: null,
              programs: [],
              year: 2016 // TODO: need to double check
            });
          }
        });
      }

      function addIncompletePrograms() {
        _.each(vm.outcomes, function(outcome) {
          if (outcome.name != vm.state.parameter.short) {
            return;
          }
          var pop = outcome.pop;

          if (vm.state.parameter.coverage == 1) {
            return;
          }

          _.each(outcome.years, function(year) {

            var existingProgramShorts = _.pluck(year.programs, 'name');
            var missingProgramShorts = [];
            var population = _.find(vm.state.parameter.populations, function(population) {
              return "" + population.pop == "" + pop;
            });
            if (population) {
              _.each(population.programs, function(program) {
                if (existingProgramShorts.indexOf(program.short) < 0) {
                  missingProgramShorts.push(program.short);
                }
              });
            }

            _.each(missingProgramShorts, function(short) {
              year.programs.push({
                name: short,
                intercept_lower: null,
                intercept_upper: null
              });
            });
          });
        });
      }

      function buildParameterSelectors() {
        vm.interactSelector = [
          {'value': 'random', 'label': 'random'},
          {'value': 'nested', 'label': 'nested'},
          {'value': 'additive', 'label': 'additive'}
        ];

        vm.populationSelector = [];
        _.each(vm.state.parameter.populations, function(population) {
          vm.populationSelector.push({
            'label': makePopulationLabel(population),
            'value': population.pop
          });
        });

        function hasNotBeenAdded(program, programSelector) {
          return _.filter(programSelector, {'value': program.short}).length == 0;
        }

        vm.programSelector = [{'label': '<none>', 'value': ''}];
        _.each(vm.state.parameter.populations, function(population) {
          _.each(population.programs, function(program) {
            if (hasNotBeenAdded(program, vm.programSelector)) {
              vm.programSelector.push({'label': program.name, 'value': program.short});
            }
          })
        });
      }

      vm.changeTargetParameter = function() {
        addIncompletePops();
        addMissingYear();
        addIncompletePrograms();
        projectService.getActiveProject();
        vm.state.targetedOutcomes = _.filter(vm.outcomes, function(outcome) {
          return outcome.name == vm.state.parameter.short;
        });
        console.log('changeTargetParameter outcomes', vm.state.targetedOutcomes);
        buildParameterSelectors();
      };

      // RECONCILE FUNCTIONS

      vm.updateSummary = function() {
        rpcService.rpcRun(
          'load_reconcile_summary',
          [vm.project.id, vm.state.progset.id, vm.state.parset.id, vm.state.year])
        .then(function(response) {
          vm.state.summary = response.data;
          console.log('updateSummary renconcile', response.data);
        });
      };

      function makeWorkType(project_id, parset_id, progset_id, year) {
        var tokens = [project_id, parset_id, progset_id, year];
        return "reconcile:" + tokens.join(":");
      }

      vm.selectSummary = function() {
        rpcService
          .rpcAsyncRun(
            'check_if_task_started', [makeTaskId()])
          .then(function(response) {
            if (response.data.status === 'started') {
              initReconcilePoll();
            }
          });
      };

      function makeTaskId() {
        return 'reconcile:'
          + vm.project.id + ":"
          + vm.state.progset.id + ":"
          + vm.state.parset.id + ":"
          + vm.state.year;
      }

      function initReconcilePoll() {
        var workType = makeWorkType(
          vm.project.id, vm.state.progset.id, vm.state.parset.id, vm.state.year);
        pollerService.startPollForRpc(
          vm.project.id,
          makeTaskId(),
          function (response) {
            var calcState = response.data;
            if (calcState.status === 'completed') {
              vm.state.statusMessage = '';
              toastr.success('Reconcile completed');
              rpcService
                .rpcRun(
                  'push_project_to_undo_stack', 
                  [vm.project.id]);
                loadReconcileData();
            } else if (calcState.status === 'started') {
              var start = new Date(calcState.start_time);
              var now = new Date(calcState.current_time);
              var diff = now.getTime() - start.getTime();
              var seconds = parseInt(diff / 1000);
              vm.state.statusMessage = "Reconcile running for " + seconds + " s";
            } else {
              vm.state.statusMessage = 'Reconcile failed';
            }
          }
        );
      }

      vm.reconcilePrograms = function() {
        rpcService.rpcAsyncRun(
          'launch_task',
          [
            makeTaskId(),
            'reconcile',
            [
              vm.project.id,
              vm.state.progset.id,
              vm.state.parset.id,
              vm.state.year,
              vm.state.maxtime
            ]
          ])
        .success(function(data) {
          initReconcilePoll();
          toastr.success('Reconcile started...');
        });
      };


      initialize();

    });

  return module;

});


