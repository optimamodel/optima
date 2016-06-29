define(['./../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller(
      'ModelCostCoverageController',
      function ($scope, toastr, $http, $state, activeProject, modalService) {

    var vm = this;

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    function initialize() {
      vm.openProject = activeProject.data;
      console.log('vm.openProject', vm.openProject);

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

      vm.selectTab = selectTab;
      vm.submit = submitOutcomeSetsOfProgset;
      vm.changeParameter = changeParameter;
      vm.changeProgsetAndParset = changeProgsetAndParset;

      var start = vm.openProject.dataStart;
      var end = vm.openProject.dataEnd;
      var years = _.range(start, end+1);
      vm.yearSelector = _.map(years, function(y) { return {'label': y, 'value': y} });

      // Stop here if spreadsheet has not been uploaded
      if (!vm.openProject.has_data) {
        modalService.inform(
          function () { },
          'Okay',
          'Please upload spreadsheet to proceed.',
          'Cannot proceed'
        );
        $state.go('project.open');
        return;
      }

      // Fetch progsets
      vm.progsets = [];
      $http.get('/api/project/' + vm.openProject.id + '/progsets')
      .success(function (response) {
        vm.progsets = response.progsets;
        vm.selectedProgset = vm.progsets[0];

        // Fetch parsets (independent of progset)
        $http.get(
          '/api/project/' + vm.openProject.id + '/parsets')
        .success(function (response) {
          vm.parsets = response.parsets;
          console.log('vm.parsets', vm.parsets);
          vm.selectedParset = vm.parsets[0];
          console.log('vm.selectedParset', vm.selectedParset);
          changeProgsetAndParset();
        });
      });
    }

    function changeProgsetAndParset() {
      if (vm.selectedProgset === undefined) {
        return;
      }
      function isActive(program) {
        return program.targetpars && program.targetpars.length > 0 && program.active;
      }
      vm.programs = _.sortBy(_.filter(vm.selectedProgset.programs, isActive), 'name');

      // Fetch outcomes for this progset
      $http.get(
        '/api/project/' + vm.openProject.id
        + '/progsets/' + vm.selectedProgset.id
        + '/effects')
      .success(function (response) {
        vm.outcomeSets = response.effects;
        console.log('outcome sets =', vm.outcomeSets);
        changeParset();
      })
    }

    function getOutcomeSetForSelectedParset() {
      var outcomeSets = _.filter(vm.outcomeSets, {parset: vm.selectedParset.id});
      if (outcomeSets.length === 0) {
        var newOutcomeSet = {
          parset: vm.selectedParset.id,
          parameters: []
        };
        vm.outcomeSets.push(newOutcomeSet);
        return newOutcomeSet;
      } else {
        return outcomeSets[0];
      }
    }

    function getOutcomesForSelectedParset() {
      return getOutcomeSetForSelectedParset().parameters;
    }

    function submitOutcomeSetsOfProgset() {
      var outcomeSets = vm.outcomeSets;
      console.log('submitting outcomes', outcomeSets);
      $http.put(
        '/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgset.id + '/effects',
        outcomeSets)
      .success(function (result) {
        toastr.success('Outcomes were saved');
        vm.outcomeSets = result.effects;
        changeParameter();
      });
    }

    function changeParset() {
      console.log('vm.selectedParset', vm.selectedParset);
      if (vm.selectedProgset && vm.selectedParset) {
        // todo: parse the parsets directly here
        $http.get(
          '/api/project/' + vm.openProject.id
          + '/progsets/' + vm.selectedProgset.id
          + '/parameters/' + vm.selectedParset.id)
        .success(function (parameters) {
          vm.parameters = parameters;
          console.log('vm.parameters', vm.parameters);
          vm.selectedParameter = vm.parameters[0];
          vm.changeParameter();
        });
      }
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function makePopKeyLabel(popKey) {
      return typeof popKey === 'string' ? popKey : popKey.join(' <-> ');
    }

    function makePopulationLabel(population) {
      var popKey = population.pop;
      return typeof popKey === 'string' ? popKey : popKey.join(' <-> ');
    }

    function extractLabelFromSelector(selector, value) {
      var option = _.find(selector, function(option) {
        // hack: compare stringified lists
        return "" + option.value === "" + value;
      });
      return option ? option.label : value;
    }

    function getOptVal(val, defaultVal) {
      if (val === "" || _.isUndefined(val)) {
        return defaultVal;
      }
      return val;
    }

    function getProgramName(short) {
      var selector = _.findWhere(vm.programSelector, {value:short});
      return selector.label;

    }

    function addIncompletePops() {

      var outcomes = getOutcomesForSelectedParset();
      var existingPops = [];

      _.each(outcomes, function (outcome) {
        if (outcome.name == vm.selectedParameter.short) {
          existingPops.push(outcome.pop);
        }
      });

      var missingPops = [];
      _.each(vm.selectedParameter.populations, function (population) {
        var findPop = _.find(existingPops, function (pop) {
          return "" + pop == "" + population.pop
        });
        if (!findPop) {
          missingPops.push(population.pop);
        }
      });

      _.each(missingPops, function(pop) {
        outcomes.push({
          name: vm.selectedParameter.short,
          pop: pop,
          years: [{
            interact: "random",
            intercept_lower: null,
            intercept_upper: null,
            programs: [],
            year: 2016 // TODO: need to double check

          }]
        })
      });

    }

    function addIncompletePrograms() {

      _.each(getOutcomesForSelectedParset(), function (outcome) {

        if (outcome.name != vm.selectedParameter.short) {
          return;
        }

        var pop = outcome.pop;

        _.each(outcome.years, function (year) {

          var existingProgramShorts = _.pluck(year.programs, 'name');
          var missingProgramShorts = [];
          var population = _.find(vm.selectedParameter.populations, function (population) {
            return "" + population.pop == "" + pop;
          });
          if (population) {
            _.each(population.programs, function (program) {
              if (existingProgramShorts.indexOf(program.short) < 0) {
                missingProgramShorts.push(program.short);
              }
            });
          }

          _.each(missingProgramShorts, function (short) {
            year.programs.push({
              name: short,
              intercept_lower: null,
              intercept_upper: null
            });
          });

        });
      });

    }

    function hasNotBeenAdded(program, programSelector) {
      return _.filter(programSelector, { 'value': program.short }).length == 0;
    }

    function buildParameterSelectors() {
      vm.interactSelector = [
        {'value': 'random', 'label': 'random'},
        {'value': 'nested', 'label': 'nested'},
        {'value': 'additive', 'label': 'additive'}
      ];

      vm.populationSelector = [];
      _.each(vm.selectedParameter.populations, function(population) {
        vm.populationSelector.push({
          'label': makePopulationLabel(population),
          'value': population.pop
        });
      });

      vm.programSelector = [{'label': '<none>', 'value': ''}];
      _.each(vm.selectedParameter.populations, function(population) {
        _.each(population.programs, function(program) {
          if (hasNotBeenAdded(program, vm.programSelector)) {
            vm.programSelector.push({'label': program.name, 'value': program.short});
          }
        })
      });
    }

    function makeBlankRow() {
      var blankCell = {label: '', attr: {style: "padding:1px"}};
      var blankCells = _(6).times(function() { return angular.copy(blankCell); });
      return {
        attr: {
          style: "background-color:#DDD",
          isEdit: false,
          isSkip: true
        },
        cells: blankCells
      };
    }

    function makeEditFn(row) {
      function innerFn() { row.attr.isEdit = true; }
      return innerFn;
    }

    function makeAcceptEditFn(row) {
      function innerFn() {
        console.log('accept');
        row.attr.isEdit = false;
        validateTable();
      }
      return innerFn;
    }

    function buildTable() {

      vm.table = {
        titles: [
          'Population / Partnerships', 'Year', 'Program Impact', 'Interact',
          'Parameter Values - Low', 'Parameter Values - High'],
        attr: {},
        rows: []
      };

      var cells;

      // vm.table.rows.push(makeBlankRow());

      // cells = [
      //   {}, {},
      //   {attr: {type: "string"}, value: 'Absolute limits of parameter values'},
      //   {},
      //   {attr: {type: "string"}, value: vm.selectedParameter.limits[0]},
      //   {attr: {type: "string"}, value: vm.selectedParameter.limits[1]}];
      // vm.table.rows.push({attr: {isSkip: true}, cells: cells});

      _.each(getOutcomesForSelectedParset(), function (outcome) {
        if (outcome.name == vm.selectedParameter.short) {
          _.each(outcome.years, function (year) {

            var pop = outcome.pop;

            vm.table.rows.push(makeBlankRow());

            cells = [];
            cells.push({label: makePopKeyLabel(pop), value: pop, attr: {type: "string"}});
            cells.push({value: year.year, attr: {type: "string"}});
            cells.push({
              label: 'Parameter values in the absence of any program',
              attr: {type: "string"}
            });
            cells.push({
              value: year.interact,
              attr: {
                type: "selector",
                options: [
                  {label: "random", value: "random"},
                  {label: "nested", value: "nested"},
                  {label: "additive", value: "additive"}
                ]
              }
            });
            cells.push({value: year.intercept_lower, attr: {type: "input"}});
            cells.push({value: year.intercept_upper, attr: {type: "input"}});

            var row = {attr: {isEdit: false}, cells: cells};
            row.attr.startEdit = makeEditFn(row);
            row.attr.acceptEdit = makeAcceptEditFn(row);
            vm.table.rows.push(row);

            _.each(year.programs, function (program) {
              cells = [{}, {}];
              cells.push({
                label: 'Maximal achievable parameter values under "'
                        + getProgramName(program.name)
                        + '"',
                value: program.name,
                attr: {type: "string"}
              });
              cells.push({});
              cells.push({value: program.intercept_lower, attr: {type: "input"}});
              cells.push({value: program.intercept_upper, attr: {type: "input"}});

              var row = {attr: {isEdit: false}, cells: cells};
              row.attr.startEdit = makeEditFn(row);
              row.attr.acceptEdit = makeAcceptEditFn(row);
              vm.table.rows.push(row);
            });
          });
        }
      });
    }

    function validateTable() {
      console.log("submit table", angular.copy(vm.table.rows));
      var parShort = vm.selectedParameter.short;
      var outcome;
      var year;
      var programs;
      var newOutcomes = [];

      _.each(vm.table.rows, function(row) {
        if (row.attr.isSkip) {
          return;
        }

        if (row.cells[0].value) {
          outcome = {
            name: parShort,
            pop: row.cells[0].value,
            years: []
          };

          year = {
            year: row.cells[1].value,
            interact: row.cells[3].value,
            intercept_lower: row.cells[4].value,
            intercept_upper: row.cells[5].value,
            programs: []
          };
          outcome.years.push(year);

          programs = year.programs;

          newOutcomes.push(outcome);
          return;
        }

        programs.push({
          name: row.cells[2].value,
          intercept_lower: row.cells[4].value,
          intercept_upper: row.cells[5].value,
        });
      });

      var iteratee = _.iteratee({'name': parShort});
      var outcomeSet = getOutcomeSetForSelectedParset();
      var oldOutcomes = _.filter(outcomeSet.parameters, iteratee);
      var keepOutcomes = _.reject(outcomeSet.parameters, iteratee);
      outcomeSet.parameters = keepOutcomes.concat(newOutcomes);

      consoleLogJson("old outcomes", oldOutcomes);
      consoleLogJson("new outcomes", newOutcomes);

      submitOutcomeSetsOfProgset();
    }

    function changeParameter() {
      addIncompletePops();
      addIncompletePrograms();
      buildParameterSelectors();
      buildTable();
    }

    initialize();

  });

});
