define(['./../module', 'underscore'], function(module, _) {

  'use strict';

  module.controller(
    'ModelCostCoverageController',
    function($scope, toastr, $http, $state, activeProject, modalService) {

      var vm = this;

      function initialize() {
        vm.project = activeProject.data;
        console.log('vm.project', vm.project);

        vm.activeTab = 'cost';
        vm.tabs = [
          {
            name: 'Define cost functions',
            slug: 'cost'
          },
          {
            name: 'Define outcome functions',
            slug: 'outcome'
          }
        ];

        vm.state = {};
        vm.progsets = [];
        vm.parsets = [];

        vm.state.yearSelector = _.range(
          vm.project.dataStart, vm.project.dataEnd+1);

        // Stop here if spreadsheet has not been uploaded
        vm.isMissingData = !vm.project.hasParset;
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

        // Fetch progsets
        $http
          .get(
            '/api/project/' + vm.project.id + '/progsets')
          .success(function(response) {
            vm.progsets = response.progsets;
            vm.state.progset = vm.progsets[0];

            // Fetch parsets (independent of progset)
            $http
              .get(
                '/api/project/' + vm.project.id + '/parsets')
              .success(function(response) {
                vm.parsets = response.parsets;
                console.log('vm.parsets', vm.parsets);
                vm.state.parset = vm.parsets[0];
                vm.changeProgsetAndParset();
              });
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
        console.log('vm.state.parset', vm.state.parset);
        if (vm.state.progset && vm.state.parset) {
          $http
            .get(
              '/api/project/' + vm.project.id
                + '/progsets/' + vm.state.progset.id
                + '/parameters/' + vm.state.parset.id)
            .success(function(parameters) {
              vm.parameters = parameters;
              console.log('vm.parameters', vm.parameters);
              vm.state.parameter = vm.parameters[0];
              vm.changeTargetParameter();
            });
        }
      }

      vm.changeProgram = function() {
        $http
          .get(
            '/api/project/' + vm.project.id
              + '/progsets/' + vm.state.progset.id
              + '/program/' + vm.state.program.id
              + '/parset/' + vm.state.parset.id
              + '/popsizes')
          .success(function(response) {
            console.log('Est populations for program', response);
            vm.state.popsizes = response;
            buildCostFunctionTables();
            vm.updateCostCovGraph();
          });
      };

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
        vm.state.program = vm.programs[0];
        if (!("attr" in vm.state.program)) {
          console.log('new attr for program');
          vm.state.program.attr = {caption: "", xupperlim: null};
        }
        console.log('selected program', vm.state.program);
        vm.state.popsizes = {};

        // Fetch outcomes for this progset
        $http
          .get(
            '/api/project/' + vm.project.id
              + '/progsets/' + vm.state.progset.id
              + '/effects')
          .success(function(response) {
            vm.outcomes = response;
            console.log('outcome summaries', vm.outcomes);
            changeParset();
            vm.changeProgram();
          })
      };

      vm.updateCostCovGraph = function() {
        vm.chartData = {};
        var years = vm.state.program.ccopars.t;
        if (_.isUndefined(years) || years.length == 0) {
          vm.chartData = null;
          return;
        }
        var url = '/api/project/' + vm.project.id
          + '/progsets/' + vm.state.progset.id
          + '/programs/' + vm.state.program.id
          + '/costcoverage/graph?t=' + years.join(',')
          + '&parset_id=' + vm.state.parset.id;
        $http
          .get(
            url)
          .success(
            function(data) {
              vm.state.chartData = data;
            })
          .error(
            function() {
              console.log('Failed to load graph for', vm.state.program.short);
            }
          );
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

      vm.saveProgram = function() {
        revertCcoparsTable();
        console.log('saving program', vm.state.program);
        $http
          .post(
            '/api/project/' + vm.project.id
              + '/progsets/' + vm.state.program.progset_id
              + '/program',
            {'program': vm.state.program})
          .success(function() {
            toastr.success('Cost data were saved');
            vm.updateCostCovGraph();
          });
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

      vm.saveProgsetOutcomes = function() {
        $http.put(
          '/api/project/' + vm.project.id
            + '/progsets/' + vm.state.progset.id
            + '/effects',
          getFilteredOutcomes(vm.outcomes))
        .success(function(response) {
          toastr.success('Outcomes were saved');
          vm.outcomes = response;
          vm.changeTargetParameter();
        });
      };

      vm.selectTab = function(tab) {
        vm.activeTab = tab;
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
        console.log('existing pop in outcome', existingPops);

        var missingPops = [];
        _.each(vm.state.parameter.populations, function(population) {
          var findPop = _.find(existingPops, function(pop) {
            return "" + pop == "" + population.pop
          });
          if (!findPop) {
            missingPops.push(population.pop);
          }
        });
        console.log('missing pop in outcome', missingPops);

        _.each(missingPops, function(pop) {
          outcomes.push({
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
        vm.state.targetedOutcomes = _.filter(vm.outcomes, function(outcome) {
          return outcome.name == vm.state.parameter.short;
        });
        console.log('selected outcomes', vm.state.targetedOutcomes);
        buildParameterSelectors();
      };

      initialize();

    });

});


// $scope.Math = window.Math;

// ccDataForm.cost.$setValidity("required", !angular.isUndefined($scope.state.newCCData.cost));
// ccDataForm.coverage.$setValidity("required", !angular.isUndefined($scope.state.newCCData.coverage));
// ccDataForm.year.$setValidity("valid", isValidCCDataYear());

// var isValidCCDataYear = function() {
//   if ($scope.state.newCCData.year) {
//     if ($scope.state.newCCData.year >= $scope.vm.project.dataStart ||
//       $scope.state.newCCData.year <= $scope.vm.project.dataEnd) {
//       var recordExisting = _.filter($scope.state.ccData, function(ccData) {
//         return ccData.year === $scope.state.newCCData.year;
//       });
//       if(recordExisting.length === 0) {
//         return true;
//       }
//     }
//   }
//   return false;
// };

// cpDataForm.splower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_lower));
// cpDataForm.spupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.saturationpercent_upper));
// cpDataForm.uclower.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_lower));
// cpDataForm.ucupper.$setValidity("required", !angular.isUndefined($scope.state.newCPData.unitcost_upper));
// cpDataForm.year.$setValidity("valid", isValidCPDataYear());

// var isValidCPDataYear = function() {
//   if ($scope.state.newCPData.year) {
//     if ($scope.state.newCPData.year >= $scope.vm.project.dataStart ||
//       $scope.state.newCPData.year <= $scope.vm.project.dataEnd) {
//       var recordExisting = _.filter($scope.state.cpData, function(cpData) {
//         return cpData.year === $scope.state.newCPData.year;
//       });
//       if(recordExisting.length === 0) {
//         return true;
//       }
//     }
//   }
//   return false;
// };