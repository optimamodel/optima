define(['angular'], function (module) {
	'use strict';

	return angular.module('app.program-scenarios-modal', [])
	.controller('ProgramScenariosModalController', function ($scope, $modalInstance, modalService, scenarios, scenario, parsets, progsets, ykeys, openProject) {
		$scope.row = scenario;
		$scope.parsets = parsets;
		$scope.progsets = progsets;
		$scope.ykeys = ykeys.data.keys;
		$scope.openProject = openProject.populations;

		$scope.progsetsOptimized = _.filter(progsets[0].programs, {active: true});

		if(!$scope.row.years) {
			$scope.row.years = [];
		}
		$scope.temp = Array($scope.row.years.length);
		$scope.type = $scope.row.scenario_type.toLowerCase();

		if (!$scope.row[$scope.type]) {
			$scope.row[$scope.type] = [];
			_.forEach($scope.progsetsOptimized, function (progset) {
				$scope.row[$scope.type].push(
					{'program': progset.short_name, 'values': []}
					);
			});
		}

		$scope.manageScenario = function(){
			var row = {
				"scenario_type": $scope.type,
				"name": $scope.row.name, 
				"parset_id": $scope.row.parset_id || null,
				"active": true, 
				"years": $scope.row.years,
				"id": $scope.row.id || null,
				"progset_id": $scope.row.progset_id.id || null
			};
			row[$scope.type] = $scope.row[$scope.type];
			$modalInstance.close(row);
		};

		$scope.addParam = function(row) {
			$scope.temp.push({});
		};

		$scope.removeParam = function(row, paramIndex) {
			$scope.temp = _.reject(row, function (param, index) {
				return index === paramIndex
			});
			if(angular.isDefined($scope.row.years[paramIndex])){
				$scope.row.years.splice(paramIndex, 1);
			}
			if(angular.isDefined($scope.row[$scope.type]) && ($scope.row[$scope.type].length > 0)){
				angular.forEach($scope.row[$scope.type], function(val, key){
					val.values.splice(paramIndex, 1);
				});
			}
		};

		$scope.scenarioExists = function(){
          return _.some(scenarios, function (scenario) {
            return $scope.row.name === scenario.name && $scope.row.id !== scenario.id;
          });
        }
	});
});
