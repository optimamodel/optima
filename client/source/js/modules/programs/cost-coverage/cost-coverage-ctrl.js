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

        // Fetch parset limits (independent of parset and progset)
        $http.get(
          '/api/project/' + vm.openProject.id + '/parsets/limits')
        .success(function (response) {
          vm.allParsetsLimits = response;

          // Fetch parsets (independent of progset)
          $http.get(
            '/api/project/' + vm.openProject.id + '/parsets')
          .success(function (response) {
            vm.parsets = response.parsets;
            console.log('vm.parsets', vm.parsets);
            vm.selectedParset = vm.parsets[0];
            changeParset()
          });
        })
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

        vm.selectedParsetLimits = vm.allParsetsLimits.parsets[vm.selectedParset.id];

        // fetch target parameters of this progset/parset combo
        $http.get(
          '/api/project/' + vm.openProject.id
          + '/progsets/' + vm.selectedProgset.id
          + '/parameters/' + vm.selectedParset.id)
        .success(function (parameters) {
          console.log('loading target parameters=', parameters);
          // {
          //   "name": "hivtest",
          //   "coverage": false,
          //   "populations": [
          //     {
          //       "pop": "FSW",
          //       "programs": [
          //         {
          //           "short": "FSW programs",
          //           "name": "Programs for female sex workers and clients"
          //         },
          //         {
          //           "short": "HTC",
          //           "name": "HIV testing and counseling"
          //         }
          //       ]
          //     },
          console.log('fetch progset/parset parameters', parameters);
          function addParsetProperties(parameter) {
            return _.extend(parameter, vm.selectedParset.pars[0][parameter.name]) ;
          }
          vm.parameters = _.map(parameters, addParsetProperties);
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

    function yearSelector(row) {
      var start = vm.openProject.dataStart;
      var end = vm.openProject.dataEnd;
      var years = _.range(start, end+1);
      var result = _.map(years, function(y) { return {'label': y, 'value': y} });
      return result;
    }

    function makeInteractSelector(row) {
      return [
        {'value':'random','label':'random'},
        {'value':'nested','label':'nested'},
        {'value':'additive','label':'additive'}
      ]
    }

    function makePopulationSelector(row) {
      var selector = [];
      _.each(vm.selectedParameter.populations, function(population) {
        selector.push({
          'label':makePopulationLabel(population),
          'value':population.pop
        });
      });
      return selector;
    }

    function makeProgramSelectors(row) {
      var selectors = [];
      function hasBeenAdded(program) {
        return _.filter(selectors, {'value': program.short}).length > 0;
      }
      _.each(vm.selectedParameter.populations, function(population) {
        _.each(population.programs, function(program) {
          if (!hasBeenAdded(program)) {
            selectors.push({ 'label': program.name, 'value': program.short });
          }
        })
      });
      selectors.splice(0, 0, {'label':'<none>', 'value':''});
      return selectors;
    }

    function validateTable(table) {
      console.log(table.rows);
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
          yearSelector,
          null, null,
          makeProgramSelectors,
          null,
          null,
          makeProgramSelectors,
          null,
          null,
          makeInteractSelector
        ],
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
      buildTable();
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
