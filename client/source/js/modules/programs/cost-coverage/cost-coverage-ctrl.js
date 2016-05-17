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
      vm.submit = submit;
      vm.changeParameter = changeParameter;
      vm.changeDropdown = changeDropdown;

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
      $http.get(
        '/api/project/' + vm.openProject.id + '/progsets')
      .success(function (response) {
        vm.progsets = response.progsets;
        vm.selectedProgset = vm.progsets[0];
        changeProgset();

        // Fetch parsets (independent of progset)
        $http.get(
          '/api/project/' + vm.openProject.id + '/parsets')
        .success(function (response) {
          vm.parsets = response.parsets;
          console.log('vm.parsets', vm.parsets);
          vm.selectedParset = vm.parsets[0];
          changeParset()
        });
      });
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function changeDropdown() {
      changeProgset();
      changeParset();
    }

    function fetchOutcomeSets(progsetId) {
      $http.get(
        '/api/project/' + vm.openProject.id
        + '/progsets/' + vm.selectedProgset.id
        + '/effects')
      .success(function (response) {
        console.warn('loading effects=', response);
        vm.outcomeSets = response.effects;
      })
    }

    function changeProgset() {
      if (vm.selectedProgset === undefined) {
        return;
      }
      function isProgramActive(program) {
        return program.targetpars && program.targetpars.length > 0 && program.active;
      }
      var allPrograms = vm.selectedProgset.programs;
      vm.programs = _.sortBy(_.filter(allPrograms, isProgramActive), 'name');

      if (_.isUndefined(vm.outcomeSets)) {
        fetchOutcomeSets();
      }
    }

    function changeParset() {
      console.log('selected parset=', vm.selectedParset);
      if (vm.selectedProgset && vm.selectedProgset.targetpartypes && vm.selectedParset) {

        // fetch target parameters of this progset/parset combo
        $http.get(
          '/api/project/' + vm.openProject.id
          + '/progsets/' + vm.selectedProgset.id
          + '/parameters/' + vm.selectedParset.id)
        .success(function (parameters) {
          console.log('loading target parameters=', parameters);
          vm.parameters = parameters;
          vm.selectedParameter = vm.parameters[0];
          vm.changeParameter();
        });
      }
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

    function makePopulationLabel(population) {
      var popKey = population.pop;
      return typeof popKey === 'string' ? popKey : popKey.join(' <-> ');
    }

    function getYearSelector(row) {
      return vm.yearSelector;
    }

    function makeInteractSelector(row) {
      return vm.interactSelector;
    }

    function makePopulationSelector(row) {
      return vm.populationSelector;
    }

    function makeProgramSelectors(row) {
      return vm.programSelector;
    }

    function validateTable(table) {
      console.log(table.rows);
    }

    function hasBeenAdded(program, selector) {
      return _.filter(selector, { 'value': program.short }).length > 0;
    }

    function resetSelectors() {
      var currPop = vm.populationSelector[0].value;
      var iEditRow = vm.parTable.iEditRow;
      if (!_.isUndefined(iEditRow)) {
        currPop = vm.parTable.rows[iEditRow][0];
      }

      vm.populationProgramSelector = [{ 'label': '<none>', 'value': '' }];
      _.each(vm.selectedParameter.populations, function (population) {
        _.each(population.programs, function (program) {
          if (population.pop == currPop) {
            if (!hasBeenAdded(program, vm.populationProgramSelector)) {
              vm.populationProgramSelector.push({ 'label': program.name, 'value': program.short });
            }
          }
        })
      });

      vm.parTable.options = [
        vm.populationSelector,
        vm.yearSelector,
        null,
        null,
        vm.populationProgramSelector,
        null,
        null,
        vm.populationProgramSelector,
        null,
        null,
        vm.interactSelector
      ];
    }

    function buildTable() {

      vm.parTable = {
        titles: [
          "Pop",
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
        widths: [],
        displayRowFns: [
          null, null, null, null, null, null, null, null, null],
        selectors: [
          makePopulationSelector,
          getYearSelector,
          null, null,
          makeProgramSelectors,
          null,
          null,
          makeProgramSelectors,
          null,
          null,
          makeInteractSelector
        ],
        updateFn: resetSelectors,
        validateFn: validateTable
      };

      _.each(getOutcomesForSelectedParset(), function(outcome) {
        if (outcome.name == vm.selectedParameter.short) {
          _.each(outcome.years, function (year) {

            var table = [
              "" + outcome.pop,
              year.year,
              year.intercept_lower,
              year.intercept_upper
            ];

            var restOfTable = [
                "",
                "",
                "",
                "",
                "",
                "",
                ""
              ];

            if (!vm.selectedParameter.coverage) {
              if (year.programs.length == 1) {
                var program = year.programs[0];
                restOfTable = [
                  program.name,
                  program.intercept_lower,
                  program.intercept_upper,
                  "<none>",
                  "",
                  "",
                  ""
                ];
              } else {
                var program0 = year.programs[0];
                var program1 = year.programs[1];
                table = table.concat([
                  program0.name,
                  program0.intercept_lower,
                  program0.intercept_upper,
                  program1.name,
                  program1.intercept_lower,
                  program1.intercept_upper,
                  program0.interact,
                ]);

              }
            }

            table = table.concat(restOfTable);
            vm.parTable.rows.push(table);

          });
        }
      });
      console.log('parTable', vm.parTable);
    }

    function changeParameter() {
      consoleLogJson("vm.selectedParameter", vm.selectedParameter);

      vm.interactSelector = [
        {'value':'random','label':'random'},
        {'value':'nested','label':'nested'},
        {'value':'additive','label':'additive'}
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
          if (!hasBeenAdded(program, vm.programSelector)) {
            vm.programSelector.push({ 'label': program.name, 'value': program.short });
          }
        })
      });

      buildTable();

      resetSelectors();

    }

    function submit() {
      if (vm.TableForm.$invalid) {
        console.error('form is invalid!');
        return false;
      }
      console.log('submitting effects=', vm.outcomeSets);
      $http.put(
        '/api/project/' + vm.openProject.id
        + '/progsets/' + vm.selectedProgset.id
        + '/effects', vm.outcomeSets)
      .success(function (result) {
        console.log('returned effects=', result);
        vm.outcomeSets = result.effects;
        toastr.success('Outcomes were successfully saved!', 'Success');
      });
    }

    initialize();

  });

});
