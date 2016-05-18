define(['./../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller(
      'ModelCostCoverageController',
      function ($scope, toastr, $http, $state, activeProject, modalService, $modal, projectApiService) {

    var vm = this;

    vm.openProject = activeProject.data;
    console.log('vm.openProject', vm.openProject);

    vm.activeTab = 'outcome';
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

    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    function initialize() {
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
        console.log('loading progset outcome sets =', response);
        vm.outcomeSets = response.effects;
        changeParset();
      })
    }

    function getOutcomesForSelectedParset() {
      var outcomeSets = _.filter(vm.outcomeSets, {parset: vm.selectedParset.id});
      if (outcomeSets.length === 0) {
        var newOutcomeSet = {
          parset: vm.selectedParset.id,
          parameters: []
        };
        vm.outcomeSets.push(newOutcomeSet);
        return newOutcomeSet.parameters;
      } else {
        return outcomeSets[0].parameters;
      }
    }

    function submitOutcomeSetsOfProgset() {
      var outcomeSets = vm.outcomeSets;
      console.log('submitting outcomes for', vm.selectedParset.name, '=', outcomeSets);
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
      console.log('selected parset =', vm.selectedParset);
      if (vm.selectedProgset && vm.selectedProgset.targetpartypes && vm.selectedParset) {
        // fetch target parameters of this progset/parset combo
        // todo: parse the parsets directly here
        $http.get(
          '/api/project/' + vm.openProject.id
          + '/progsets/' + vm.selectedProgset.id
          + '/parameters/' + vm.selectedParset.id)
        .success(function (parameters) {
          console.log('loading targeted parameters =', parameters);
          vm.parameters = parameters;
          vm.selectedParameter = vm.parameters[0];
          vm.changeParameter();
        });
      }
    }
    function selectTab(tab) {
      vm.activeTab = tab;
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

    function getProgram1Label(row) {
      return extractLabelFromSelector(vm.programSelector, row[7]);
    }

    function getProgram2Label(row) {
      return extractLabelFromSelector(vm.programSelector, row[4]);
    }

    function getPopOrPshipLabel(row) {
      return extractLabelFromSelector(vm.populationSelector, row[0]);
    }

    function getOptVal(val, defaultVal) {
      if (val === "" || _.isUndefined(val)) {
        return defaultVal;
      }
      return val;
    }

    function validateTable(table) {
      // {
      //   "name": "condcas",
      //   "pop": [
      //     "Females 15-49",
      //     "Clients"
      //   ],
      //   "years": [
      //     {
      //       "intercept_upper": 0.4,
      //       "interact": "random",
      //       "intercept_lower": 0.3,
      //       "programs": [
      //         {
      //           "intercept_upper": 0.7,
      //           "name": "SBCC + Condoms",
      //           "intercept_lower": 0.5
      //         }
      //       ],
      //       "year": 2016
      //     }
      //   ]
      // }
      var outcomes = getOutcomesForSelectedParset();
      var parShort = vm.selectedParameter.short;

      _.each(vm.parTable.rows, function(row, iRow) {
        
        if (iRow == vm.parTable.iEditRow) {
          return;
        }

        var outcome = _.findWhere(outcomes, {'name':parShort, 'pop':row[0]});
        if (_.isUndefined(outcome)) {
          outcome = {
            name: parShort,
            pop: row[0],
            interact: "random",
            years: []
          };
          outcomes.push(outcome);
        }

        var years = outcome.years;
        var yearVal = parseInt(row[1]);
        year = _.findWhere(years, {year: yearVal});
        if (_.isUndefined(year)) {
          var year = {
            year: yearVal,
            intercept_lower: row[2],
            intercept_upper: row[3],
            interact: getOptVal(row[10], "random"),
            programs: []
          };
          years.push(year);
        } else {
          year.programs.splice(0, year.programs.length);
        }

        var program1 = row[4];
        if (program1) {
          year.programs.push({
            name: program1,
            intercept_lower: getOptVal(row[5], null),
            intercept_upper: getOptVal(row[6], null),
          })
        }
        var program2 = row[7];
        if (program2) {
          year.programs.push({
            name: program2,
            intercept_lower: getOptVal(row[8], null),
            intercept_upper: getOptVal(row[9], null)
          })
        }
      });
      submitOutcomeSetsOfProgset();
    }

    function hasNotBeenAdded(program, programSelector) {
      return _.filter(programSelector, { 'value': program.short }).length == 0;
    }

    function resetDynamicSelectors() {
      var currPop = vm.populationSelector[0].value;
      var iEditRow = vm.parTable.iEditRow;
      if (!_.isUndefined(iEditRow)) {
        currPop = vm.parTable.rows[iEditRow][0];
      }

      var firstProgramSelector = [{ 'label': '<none>', 'value': '' }];
      _.each(vm.selectedParameter.populations, function (population) {
        _.each(population.programs, function (program) {
          if (population.pop == currPop) {
            if (hasNotBeenAdded(program, firstProgramSelector)) {
              firstProgramSelector.push({
                'label': program.name, 'value': program.short });
            }
          }
        })
      });

      var secondProgramSelector = [{ 'label': '<none>', 'value': '' }];
      if (firstProgramSelector.length > 2) {
        _.each(vm.selectedParameter.populations, function (population) {
          _.each(population.programs, function (program) {
            if (population.pop == currPop) {
              if (hasNotBeenAdded(program, secondProgramSelector)) {
                secondProgramSelector.push({
                  'label': program.name, 'value': program.short
                });
              }
            }
          })
        });
      }

      vm.parTable.options = [
        vm.populationSelector,
        vm.yearSelector,
        null,
        null,
        firstProgramSelector,
        null,
        null,
        secondProgramSelector,
        null,
        null,
        vm.interactSelector
      ];
    }

    function buildTable() {

      vm.parTable = {
        titles: [
          "Population / Partnerships",
          "Year",
          "Lo",
          "Hi",
          "Program 1",
          "Lo",
          "Hi",
          "Program 2",
          "Lo",
          "Hi",
          "Interact"
        ],
        rows: [],
        types: [
          "selector", "selector",
          "number", "number",
          "selector", "number", "number",
          "selector", "number", "number",
          "selector"
        ],
        widths: ["", "", 100, 100, "", 100, 100, "", 100, 100],
        displayRowFns: [
          getPopOrPshipLabel, null, null, null, getProgram2Label, null, null, getProgram1Label, null],
        updateFn: resetDynamicSelectors,
        validateFn: validateTable
      };

      _.each(getOutcomesForSelectedParset(), function(outcome) {
        if (outcome.name == vm.selectedParameter.short) {
          _.each(outcome.years, function (year) {

            var row = [
              outcome.pop,
              year.year,
              year.intercept_lower,
              year.intercept_upper
            ];

            var restOfTable = ["", "", "", "", "", "", ""];

            if (year.programs.length == 1) {
              var program = year.programs[0];
              restOfTable = [
                program.name,
                program.intercept_lower,
                program.intercept_upper,
                "", "", "", ""
              ];
            } else if (year.programs.length == 2) {
              var program0 = year.programs[0];
              var program1 = year.programs[1];
              row = row.concat([
                program0.name,
                program0.intercept_lower,
                program0.intercept_upper,
                program1.name,
                program1.intercept_lower,
                program1.intercept_upper,
                program0.interact,
              ]);
            }

            row = row.concat(restOfTable);
            vm.parTable.rows.push(row);
          });
        }
      });
    }

    function buildParameterSelectors() {
      vm.interactSelector = [
        { 'value': 'random', 'label': 'random' },
        { 'value': 'nested', 'label': 'nested' },
        { 'value': 'additive', 'label': 'additive' }
      ];

      vm.populationSelector = [];
      _.each(vm.selectedParameter.populations, function(population) {
        vm.populationSelector.push({
          'label': makePopulationLabel(population),
          'value': population.pop
        });
      });

      vm.programSelector = [{ 'label': '<none>', 'value': '' }];
      _.each(vm.selectedParameter.populations, function (population) {
        _.each(population.programs, function (program) {
          if (hasNotBeenAdded(program, vm.programSelector)) {
            vm.programSelector.push({ 'label': program.name, 'value': program.short });
          }
        })
      });
    }

    function changeParameter() {
      console.log("vm.selectedParameter", vm.selectedParameter);
      buildParameterSelectors();
      buildTable();
      resetDynamicSelectors();
    }

    initialize();

  });

});
