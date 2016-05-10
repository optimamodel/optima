define(['./../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, toastr, $http, $state, activeProject, modalService, $modal, projectApiService) {

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
    }/*, {
     name: 'View summary',
     slug: 'summary'
     }*/];

    /* VM functions */
    vm.addYear = addYear;
    vm.selectTab = selectTab;
    vm.deleteYear = deleteYear;
    vm.submit = submit;
    vm.changeParameter = changeParameter;
    vm.changeDropdown = changeDropdown;
    vm.getPopulationTitle = getPopulationTitle;
    vm.initYearPrograms = initYearPrograms;
    vm.getFullProgramName = getFullProgramName;

    /* Function definitions */

    function consoleLogVar(name, val) {
      console.log(name + ' = ');
      console.log(JSON.stringify(val, null, 2));
    }

    function getFullProgramName(short) {
      var program = _.filter(vm.selectedProgramSet.programs, {short: short});
      if (program.length === 0) {
        return '';
      }
      return program[0].name;
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
      console.log('changing dropdown');
      setProgramSet()
      setParamSet()
    }

    function sortByName(program) {
      return program.name;
    }

    function isProgramActive(program) {
      return program.targetpars && program.targetpars.length > 0 && program.active;
    }

    function setProgramSet() {
      if (vm.selectedProgramSet !== undefined) {

        if (vm.existingEffects === undefined) {
          $http.get('/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgramSet.id + '/effects').success(function (response) {
            console.warn('response is', response);
            vm.existingEffects = response;
          })
        }

        vm.programs = _.sortBy(_.filter(vm.selectedProgramSet.programs, isProgramActive), sortByName);
      }
    }

    function setParamSet() {
      console.log('setting param set', vm.selectedParset);
      if (vm.selectedProgramSet && vm.selectedProgramSet.targetpartypes && vm.selectedParset) {

        vm.currentParsetLimits = vm.allLimits.parsets[vm.selectedParset.id];

        $http.get('/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgramSet.id + '/parameters/' + vm.selectedParset.id).success(function (response) {
          console.warn('response', response);

          vm.params = _.map(response, function (par) {
            return _.extend(par, vm.selectedParset.pars[0][par.name])
          });
          vm.selectedParameter = vm.params[0];
          vm.changeParameter();
          console.log('vm.params', vm.params);
        });

      }
    }

    function getPopulationKey(population) {
      var title = population.pop;
      var titleIsString = typeof title === 'string';
      return titleIsString ? title : title.join('+++');
    }

    function getPopulationsWithKey(populations) {
      var existingPopulations = angular.copy(getExistingPopulation(vm.selectedParset.id, vm.selectedParameter.short));

      var obj = {}

      _.each(populations, function (population) {
        var populationKey = getPopulationKey(population);
        obj[populationKey] = _.extend(population, {
          key: populationKey,
          years: [{}]
        })

        if (existingPopulations[populationKey] !== undefined) {
          obj[populationKey] = _.extend(obj[populationKey], existingPopulations[populationKey])
        }
      })

      return obj
    }

    function getYearsFromParamGroup(paramGroup) {
      var years = [];
      _.each(paramGroup, function (pg) {
        years = years.concat(_.map(pg.years, function (y) {
          return _.pick(y, ['intercept_lower', 'intercept_upper', 'year', 'interact'])
        }))
      })
      return years
    }

    function getProgramsFromParamGroup(paramGroup) {
      console.group('getProgramsFromParamGroup', paramGroup);

      var programs = [];
      _.each(paramGroup, function (pg) {
        _.each(pg.years, function (year) {
          _.each(year.programs, function (program) {
            var foundPrograms = _.filter(programs, {name: program.name});
            if (foundPrograms.length === 0) {
              console.log('program', program);
              programs.push(program)
            }
          })
        })
      })

      console.log('programs', programs);
      console.groupEnd();

      return programs;
    }

    function getExistingPopulation(parsetId, parameterShort) {
      console.group('get existing population', parsetId, parameterShort)
      var effects = vm.existingEffects.effects;
      var parametersForThisParset = _.findWhere(effects, {parset: parsetId})
      if (parametersForThisParset === undefined) {
        console.log('no existing populations')
        return [];
      }
      var currentParameterProps = _.filter(parametersForThisParset.parameters, {name: parameterShort})
      var groupedByName = _.groupBy(currentParameterProps, 'name');

      console.log('groupedByName', groupedByName);
      var existingPopulations = {}

      _.each(groupedByName, function (paramGroup) {
        console.log('paramGroup', paramGroup);

        var key = getPopulationKey(paramGroup[0]);
        existingPopulations[key] = {
          key: key,
          years: getYearsFromParamGroup(paramGroup),
          programs: getProgramsFromParamGroup(paramGroup)
        }
      })
      console.log('existingPopulations', existingPopulations);
      console.groupEnd()
      return existingPopulations;
    }

    function yearSelector(row) {
      var start = vm.openProject.dataStart;
      var end = vm.openProject.dataEnd;
      var years = _.range(start, end+1);
      var result = _.map(years, function(y) { return {'label':y, 'value':y} });
      console.log('yearSelector', result);
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
      var effect = _.findWhere(vm.existingEffects.effects, {parset: parsetId});
      var parShort = vm.selectedParameter.short;
      var pops = [];
      _.each(effect.parameters, function(parameter) {
        if (parameter.name == parShort) {
          pops.push(parameter.pop);
        }
      });
      var result = _.map(_.uniq(pops), function(p) { return {'label':p, 'value':p} });
      console.log('popselector', result);
      return result;
    }

    function progSelector(row) {
      var parsetId = vm.selectedParset.id;
      var effect = _.findWhere(vm.existingEffects.effects, {parset: parsetId});
      var names = [];
      _.each(effect.parameters, function(parameter) {
        _.each(parameter.years, function(year) {
          _.each(year.programs, function(program) {
            names.push(program.name);
          })
        })
      });
      var result = _.map(_.uniq(names), function(name) {
        return {'label':vm.getFullProgramName(name), 'value':name}
      });
      result.splice(0, 0, {'label':'<baseline>', 'value':'<baseline>'});
      console.log('progSelector', result);
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

      _.each(vm.existingEffects.effects, function(effect) {

        console.log('loop >', vm.selectedParameter.short, effect.parset);

        _.each(effect.parameters, function(parameter) {

          console.log('loop >', parameter.name, parameter.pop);

          if (parameter.name != vm.selectedParameter.short) {
            return;
          };

          _.each(parameter.years, function(year) {

            console.log('loop >>', year.year);

            vm.parTable.rows.push([
              "" + parameter.pop,
              year.year,
              "<baseline>",
              year.intercept_lower,
              year.intercept_upper,
              year.interact,
            ]);

            _.each(year.programs, function (program) {

              consoleLogVar("program", program);
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
        })

      });

      consoleLogVar('parTable', vm.parTable);
    }


    function changeParameter() {
      console.group('changing parameter', vm.selectedParameter)
      vm.currentParameter = _.extend(
        _.pick(vm.selectedParameter, ['name', 'short', 'coverage']),
        {
          populations: getPopulationsWithKey(vm.selectedParameter.populations)
        }
      );
      console.log('parameter is', vm.currentParameter);
      console.groupEnd();
      var parsetEffects = _.filter(vm.existingEffects.effects, {parset: vm.selectedParset.id});
      console.log('parsetEffects', parsetEffects);
      var currentParsetEffect;
      if (parsetEffects.length === 0) {
        currentParsetEffect = {
          parset: vm.selectedParset.id,
          parameters: []
        }
        vm.existingEffects.effects.push(currentParsetEffect);
      } else {
        currentParsetEffect = parsetEffects[0];
      }
      console.log('currentParsetEffect', currentParsetEffect);
      _.each(vm.currentParameter.populations, function(pop) {
        var paramPops = _.filter(currentParsetEffect.parameters, {name: vm.selectedParameter.short});
        paramPops = _.filter(paramPops, function(param) {
          if (pop.pop instanceof Array) {
            if (param.pop.length != pop.pop.length) {
              return false;
            }
            return _.difference(param.pop, pop.pop).length === 0;
          }
          return pop.pop === param.pop;
        });
        if (paramPops.length === 0) {
          currentParsetEffect.parameters.push({
            name: vm.selectedParameter.short,
            pop: pop.pop,
            years: []
          });
        }
      });

      buildTable();
      console.log('currentParsetEffect', currentParsetEffect);
    }

    function getParameters(currentParameter) {
      var newMap = _.map(currentParameter.populations, function (population) {
        console.log('population', population);
        return {
          name: currentParameter.short,
          pop: population.pop,
          interact: population.interact,
          years: _.map(population.years, function (year) {
            year.programs = _.map(year.programs, function (program) {
              return program
            })
            return year
          })
        }
      });
      return newMap
    }

    function submit() {
      if (vm.TableForm.$invalid) {
        console.error('form is invalid!');
        return false;
      }

      console.log('submitting', vm.existingEffects);

      // var finalJson = {
      //   effects: [
      //     {
      //       "parset": vm.selectedParset.id,
      //       "parameters": getParameters(angular.copy(vm.currentParameter))
      //     }
      //   ]
      // };

      // console.log('final result', finalJson);
      // console.log(JSON.stringify(finalJson, null, ' '))

      $http.put('/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgramSet.id + '/effects', vm.existingEffects).success(function (result) {
        console.log('result is', result);
        vm.existingEffects = result;
        toastr.success('The parameters were successfully saved!', 'Success');
      });
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function deleteYear(yearObject, yearIndex) {
      yearObject.years = _.reject(yearObject.years, function (year, index) {
        return index === yearIndex
      });
      console.log(vm.existingEffects);
    }

    function addYear(yearObject) {
      yearObject.years.push({
        id: _.random(1, 10000),
        programs: vm.initYearPrograms(yearObject.pop)
      });

    }

    $scope.$watch(function () {
      return vm.effects
    }, function () {
      console.log('current form and parameter', vm.currentParameter);
    }, true)

    /* Initialize */

    // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
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

    // Fetch list of progsets
    $http.get('/api/project/' + vm.openProject.id + '/progsets').success(function (response) {
      vm.programSetList = response.progsets;
      vm.selectedProgramSet = vm.programSetList[0];
      setProgramSet();

      // Fetch parset limits
      $http.get('/api/project/' + vm.openProject.id + '/parsets/limits').success(function (response) {
        vm.allLimits = response;

        // Fetch list of parameter-sets
        $http.get('/api/project/' + vm.openProject.id + '/parsets').success(function (response) {
          vm.parsets = response.parsets;
          vm.selectedParset = vm.parsets[0];
          setParamSet()
        });
      })
    });


  });

});
