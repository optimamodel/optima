define(['./../module', 'underscore'], function (module, _) {

  'use strict';

  module.controller(
      'ModelCostCoverageController',
      function ($scope, toastr, $http, $state, activeProject, modalService, $modal, projectApiService) {

    var vm = this;

    vm.openProject = activeProject.data;
    console.log('vm.openProject', vm.openProject);

    vm.activeTab = 'cost';
    vm.tabs = [{
      name: 'Define cost functions',
      slug: 'cost'
    }, {
      name: 'Define outcome functions',
      slug: 'outcome'
    }];


    function consoleLogJson(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    function initialize() {
      vm.addYear = addYear;
      vm.selectTab = selectTab;
      vm.deleteYear = deleteYear;
      vm.submit = submit;
      vm.changeParameter = changeParameter;
      vm.changeDropdown = changeDropdown;
      vm.getPopulationTitle = getPopulationTitle;
      vm.initYearPrograms = initYearPrograms;
      vm.getProgramName = getProgramName;

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

    function getProgramName(short) {
      var program = _.filter(vm.selectedProgset.programs, {short: short});
      return program.length === 0 ? '' : program[0].name;
    }

    function initYearPrograms(pop) {
      console.log('initYearPrograms called with', pop);
      var currentPop = _.filter(vm.selectedParameter.populations, {pop: pop});
      console.log('currentPop', currentPop);
      if (currentPop.length === 0) {
        return [];
      }
      console.log('programs', currentPop[0].programs);
      return _.map(currentPop[0].programs, function (program) {
        return {
          name: program.short
        }
      });
    }

    function getPopulationTitle(population) {
      if (population) {
        var title = population;
        return title === undefined ? '' : (typeof title === 'string' ? title : title.join(' - '))
      }
      return ''
    }

    function changeDropdown() {
      changeProgset();
      changeParset();
    }

    function fetchProgsetEffects(progsetId) {
      $http.get(
        '/api/project/' + vm.openProject.id
        + '/progsets/' + vm.selectedProgset.id
        + '/effects')
      .success(function (response) {
        console.warn('loading effects=', response);
        vm.effects = response.effects;
      })
    }

    function changeProgset() {
      if (vm.selectedProgset === undefined) {
        return;
      }
      function isProgramActive(program) {
        return program.targetpars && program.targetpars.length > 0 && program.active;
      }
      var activePrograms = _.filter(vm.selectedProgset.programs, isProgramActive);
      vm.programs = _.sortBy(activePrograms, function(p) { return p.name; });
      if (_.isUndefined(vm.effects)) {
        fetchProgsetEffects();
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

          function addParsetProperties(parameter) {
            return _.extend(parameter, vm.selectedParset.pars[0][parameter.name]) ;
          }

          vm.parameters = _.map(parameters, addParsetProperties);
          vm.selectedParameter = vm.parameters[0];
          vm.changeParameter();
          console.log('vm.parameters', vm.parameters);
        });
      }
    }

    function makePopKey(population) {
      var popKey = population.pop;
      return typeof popKey === 'string' ? popKey : popKey.join('+++');
    }

    function makePopDict() {
      var completePopDict = getAllPopInParameterDict(
          vm.selectedParset.id, vm.selectedParameter.short);
      var popDict = {};
      _.each(vm.selectedParameter.populations, function (population) {
        var popKey = makePopKey(population);
        popDict[popKey] = _.extend(population, { key: popKey, years: [{}]});
        if (!_.isUndefined(completePopDict[popKey])) {
          popDict[popKey] = _.extend(popDict[popKey], completePopDict[popKey])
        }
      });
      return popDict
    }

    function getYearsFromParameters(parameters) {
      var years = [];
      _.each(parameters, function (parameter) {
        years = years.concat(_.map(parameter.years, function (y) {
          return _.pick(y, ['intercept_lower', 'intercept_upper', 'year', 'interact'])
        }))
      })
      return years
    }

    function getProgramsFromParameters(parameters) {
      var programs = [];
      _.each(parameters, function (parameter) {
        _.each(parameter.years, function (year) {
          _.each(year.programs, function (program) {
            var foundPrograms = _.filter(programs, {name: program.name});
            if (foundPrograms.length === 0) {
              programs.push(program)
            }
          })
        })
      });
      console.log('getProgramsFromParameters', programs);
      return programs;
    }

    function getAllPopInParameterDict(parsetId, parameterShort) {
      var effect = _.findWhere(vm.effects, {parset: parsetId})
      if (effect === undefined) {
        console.log('no effects for this parameter');
        return [];
      }
      var parameter = _.filter(effect.parameters, {name: parameterShort})
      var parametersByName = _.groupBy(parameter, 'name');

      console.log('parametersByName', parametersByName);
      var popDict = {};
      _.each(parametersByName, function (parameters) {
        var key = makePopKey(parameters[0]);
        popDict[key] = {
          key: key,
          years: getYearsFromParameters(parameters),
          programs: getProgramsFromParameters(parameters)
        }
      });
      console.log('completePopDict', popDict);
      return popDict;
    }

    function yearSelector(row) {
      var start = vm.openProject.dataStart;
      var end = vm.openProject.dataEnd;
      var years = _.range(start, end+1);
      var result = _.map(years, function(y) { return {'label':y, 'value':y} });
      return result;
    }

    function interactSelector(row) {
      return [
        {'value':'random','label':'random'},
        {'value':'nested','label':'nested'},
        {'value':'additive','label':'additive'}
      ]
    }

    function popSelector(row) {
      var parsetId = vm.selectedParset.id;
      var effect = _.findWhere(vm.effects, {parset: parsetId});
      var parShort = vm.selectedParameter.short;
      var pops = [];
      _.each(effect.parameters, function(parameter) {
        if (parameter.name == parShort) {
          pops.push(parameter.pop);
        }
      });
      var result = _.map(_.uniq(pops), function(p) { return {'label':p, 'value':p} });
      return result;
    }

    function progSelector(row) {
      var parsetId = vm.selectedParset.id;
      var effect = _.findWhere(vm.effects, {parset: parsetId});
      var names = [];
      _.each(effect.parameters, function(parameter) {
        _.each(parameter.years, function(year) {
          _.each(year.programs, function(program) {
            names.push(program.name);
          })
        })
      });
      var result = _.map(_.uniq(names), function(name) {
        return {'label':vm.getProgramName(name), 'value':name}
      });
      result.splice(0, 0, {'label':'<baseline>', 'value':'<baseline>'});
      return result;
    }

    function validateTable(table) {
      console.log(table.rows);
    }

    function buildTable() {
      vm.parTable = {
        titles: [
          "Pop", "Year", "Program", "Value (lo)", "Value (hi)", "Interaction"],
        rows: [],
        types: ["selector", "selector", "selector", "number", "number", "selector"],
        widths: [],
        displayRowFns: [null, null, null, null, null, null],
        selectors: [popSelector, yearSelector, progSelector, null, null, interactSelector],
        validateFn: validateTable
      };
      _.each(vm.effects, function(effect) {
        _.each(effect.parameters, function(parameter) {
          if (parameter.name == vm.selectedParameter.short) {
            _.each(parameter.years, function (year) {
              vm.parTable.rows.push([
                "" + parameter.pop,
                year.year,
                "<baseline>",
                year.intercept_lower,
                year.intercept_upper,
                year.interact,
              ]);
              _.each(year.programs, function (program) {
                vm.parTable.rows.push([
                  "" + parameter.pop,
                  year.year,
                  program.name,
                  program.intercept_lower,
                  program.intercept_upper,
                  year.interact
                ]);

              });
            });
          }
        })
      });
      console.log('parTable', vm.parTable);
    }

    function getEffectForSelectedParset() {
      var effects = _.filter(vm.effects, {parset: vm.selectedParset.id});
      if (effects.length === 0) {
        // create a new targeted effect
        var newEffect = {
          parset: vm.selectedParset.id,
          parameters: []
        };
        vm.effects.push(newEffect);
        return newEffect;
      } else {
        return effects[0];
      }
    }

    function containsPopulation(parameters, population) {
      function hasPopulation(parameter) {
        if (population.pop instanceof Array) {
          if (parameter.pop.length != population.pop.length) {
            return false;
          }
          return _.difference(parameter.pop, population.pop).length === 0;
        }
        return population.pop === parameter.pop;
      }
      var selectedParameters = _.filter(parameters, {name: vm.selectedParameter.short});
      // consoleLogJson("selectedParameters", selectedParameters);
      return _.filter(selectedParameters, hasPopulation).length > 0;
    }

    function changeParameter() {
      var parameter = _.pick(vm.selectedParameter, ['name', 'short', 'coverage']);
      vm.currentParameter = _.extend(parameter, {populations: makePopDict()});
      console.log("vm.currentParameter", vm.currentParameter);

      // ensure effect has selected parameter and populations
      var effect = getEffectForSelectedParset();
      _.each(vm.currentParameter.populations, function(population) {
        if (!containsPopulation(effect.parameters, population)) {
          var newParameter = {
            name: vm.selectedParameter.short,
            pop: population.pop,
            years: []
          };
          effect.parameters.push(newParameter);
        }
      });
      // consoleLogJson('effect', effect);
      buildTable();
    }

    function submit() {
      if (vm.TableForm.$invalid) {
        console.error('form is invalid!');
        return false;
      }
      console.log('submitting effects=', vm.effects);
      $http.put(
        '/api/project/' + vm.openProject.id
        + '/progsets/' + vm.selectedProgset.id
        + '/effects', vm.effects)
      .success(function (result) {
        console.log('returned effects=', result);
        vm.effects = result.effects;
        toastr.success('Effects were successfully saved!', 'Success');
      });
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function deleteYear(yearObject, yearIndex) {
      yearObject.years = _.reject(yearObject.years, function (year, index) {
        return index === yearIndex
      });
      console.log(vm.effects);
    }

    function addYear(yearObject) {
      yearObject.years.push({
        id: _.random(1, 10000),
        programs: vm.initYearPrograms(yearObject.pop)
      });

    }

    initialize();

  });

});
