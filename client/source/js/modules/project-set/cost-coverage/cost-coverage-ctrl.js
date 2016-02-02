define(['./../module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http, $state, activeProject, modalService, projectApiService) {

    var vm = this;

    vm.openProject = activeProject.data;
    console.log('vm.openProject', vm.openProject);

    vm.activeTab = 'outcome'; //todo: revert to first
    vm.tabs = [{
      name: 'Define cost functions',
      slug: 'cost'
    }, {
      name: 'Define outcome functions',
      slug: 'outcome'
    }, {
      name: 'View summary',
      slug: 'summary'
    }];

    /* VM functions */
    vm.addYear = addYear;
    vm.selectTab = selectTab;
    vm.deleteYear = deleteYear;
    vm.submit = submit;
    vm.changeParameter = changeParameter;
    vm.changeDropdown = changeDropdown;
    vm.getPopulationTitle = getPopulationTitle;

    /* Function definitions */

    function getPopulationTitle(population) {
      if (population && population.pop) {
        var title = population.pop;
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
      return program.parameters && program.parameters.length > 0 && program.active;
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

        $http.get('/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgramSet.id + '/parameters/' + vm.selectedParset.id).success(function (response) {
          console.warn('response', response);

          vm.params = _.map(response, function (par) {
            return _.extend(par, vm.selectedParset.pars[0][par.name])
          });

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

      console.log('submitting', vm.currentParameter);

      var finalJson = {
        effects: [
          {
            "parset": vm.selectedParset.id,
            "parameters": getParameters(angular.copy(vm.currentParameter))
          }
        ]
      };

      console.log('final result', finalJson);
      console.log(JSON.stringify(finalJson, null, ' '))

      $http.put('/api/project/' + vm.openProject.id + '/progsets/' + vm.selectedProgramSet.id + '/effects', finalJson).success(function (result) {
        console.log('result is', result);
      })
    }

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function deleteYear(yearObject, yearIndex) {
      yearObject.years = _.reject(yearObject.years, function (year, index) {
        return index === yearIndex
      });
    }

    function addYear(yearObject) {
      yearObject.years.push({id: _.random(1, 10000)});

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
        function () {
        },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $state.go('project.open');
      return;
    }

    // Fetch list of program-set for open-project from BE
    $http.get('/api/project/' + vm.openProject.id + '/progsets').success(function (response) {
      vm.programSetList = response.progsets;
    });

    // Fetch list of parameter-set for open-project from BE
    $http.get('/api/project/' + vm.openProject.id + '/parsets').success(function (response) {
      vm.parsets = response.parsets;
    });

  });

});
