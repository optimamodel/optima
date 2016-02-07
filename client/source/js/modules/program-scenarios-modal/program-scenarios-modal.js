define(['angular'], function (module) {
  'use strict';

  return angular.module('app.program-scenarios-modal', [])
    .controller('ProgramScenariosModalController', function ($scope, $modalInstance, modalService, scenario, parsets, progsets, ykeys, openProject) {
    	$scope.row = scenario;
    	$scope.parsets = parsets;
        $scope.progsets = progsets;
        $scope.ykeys = ykeys.data.keys;
    	$scope.openProject = openProject.populations;
    	
    	$scope.progsetsOptimized = _.filter(progsets[0].programs, {optimizable: true});

    	if(!angular.isDefined($scope.row[$scope.row.scenario_type])){
    		$scope.row[$scope.row.scenario_type] = {};
    	}

    	$scope.manageScenario = function(){
    		var row = {
    			"scenario_type": $scope.row.scenario_type,
    			"name": $scope.row.name, 
    			"parset_id": $scope.row.parset_id || null,
    			"active": true, 
    			//"t": [], 
    			"id": $scope.row.id || null, 
    			"progset_id": $scope.row.progset_id || null
    		};

			row[$scope.row.scenario_type] = $scope.row[$scope.row.scenario_type];
    		$modalInstance.close(row);
    	};

        $scope.addParam = function(row) {
            if (!row.pars) {
                row.pars = [];
            }
            row.pars.push({});
        };

        $scope.removeParam = function(row, paramIndex) {
            row.pars = _.reject(row.pars, function (param, index) {
                return index === paramIndex
            });
        };

        $scope.closeModal = function() {
            $modalInstance.close($scope.row);
        };

    });
});
