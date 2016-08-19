define(['./../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller(
      'ModelCostCoverageController',
      function ($scope, toastr, $http, $state, activeProject, modalService) {

      // [
      //   {
      //     "interact": "random",
      //     "name": "numtx",
      //     "pop": "tot",
      //     "years": [
      //       {
      //         "intercept_lower": null,
      //         "intercept_upper": null,
      //         "programs": [
      //           {
      //             "name": "ART",
      //             "intercept_lower": null,
      //             "intercept_upper": null
      //           }
      //         ],
      //         "year": 2016
      //       }
      //     ]
      //   }
      // ]

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
      vm.submitOutcomes = submitOutcomes;
      vm.getProgramName = getProgramName;
      vm.makePopKeyLabel = makePopKeyLabel;
      vm.changeParameter = changeParameter;
      vm.changeProgsetAndParset = changeProgsetAndParset;

      var start = vm.openProject.dataStart;
      var end = vm.openProject.dataEnd;
      var years = _.range(start, end+1);
      vm.yearSelector = _.map(years, function(y) { return {'label': y, 'value': y} });

      // Stop here if spreadsheet has not been uploaded
      if (!vm.openProject.hasData) {
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
        vm.outcomes = response;
        console.log('outcome summaries', vm.outcomes);
        changeParset();
      })
    }

    function submitOutcomes() {
      var outcomes = angular.copy(vm.outcomes);
      consoleLogJson('submitting outcomes', outcomes);
      $http.put(
        '/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgset.id + '/effects',
        outcomes)
      .success(function (response) {
        toastr.success('Outcomes were saved');
        vm.outcomes = response;
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
      if (typeof popKey === 'string') {
        if (popKey == "tot") {
          return "Total Population";
        }
        return popKey;
      }
      return popKey.join(' <-> ');
    }

    function makePopulationLabel(population) {
      var popKey = population.pop;
      return typeof popKey === 'string' ? popKey : popKey.join(' <-> ');
    }

    function getProgramName(short) {
      var selector = _.findWhere(vm.programSelector, {value:short});
      return selector.label;
    }

    function addIncompletePops() {

      var existingPops = [];
      _.each(vm.outcomes, function(outcome) {
        if (outcome.name == vm.selectedParameter.short) {
          existingPops.push(outcome.pop);
        }
      });
      console.log('existing pop in outcome', existingPops);

      var missingPops = [];
      _.each(vm.selectedParameter.populations, function(population) {
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
          name: vm.selectedParameter.short,
          pop: pop,
          interact: "random",
          years: []
        })
      });
    }

    function addMissingYear() {
      _.each(vm.outcomes, function (outcome) {
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

      _.each(vm.outcomes, function (outcome) {

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

    function hasNotBeenAdded(program, programSelector) {
      return _.filter(programSelector, { 'value': program.short }).length == 0;
    }

      vm.programSelector = [{'label': '<none>', 'value': ''}];
      _.each(vm.selectedParameter.populations, function(population) {
        _.each(population.programs, function(program) {
          if (hasNotBeenAdded(program, vm.programSelector)) {
            vm.programSelector.push({'label': program.name, 'value': program.short});
          }
        })
      });
    }

    function changeParameter() {
      addIncompletePops();
      addMissingYear();
      addIncompletePrograms();
      vm.selectedOutcomes = _.filter(vm.outcomes, function(outcome) {
        return outcome.name == vm.selectedParameter.short;
      });
      consoleLogJson('selected outcomes', vm.selectedOutcomes);
      buildParameterSelectors();
    }

    initialize();

  });

});
