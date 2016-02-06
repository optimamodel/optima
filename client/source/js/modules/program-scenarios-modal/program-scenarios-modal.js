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

    	$scope.budget = {};
    	$scope.coverage = {};

    	if(angular.isDefined($scope.row.budget)){
    		$scope.radio = 'budget';
    		$scope.row.coverage = {};
    	}else if(angular.isDefined($scope.row.coverage)){
    		$scope.radio = 'coverage';
    		$scope.row.budget = {};
    	}else{
    		$scope.radio = 'budget';
    		$scope.row.budget = {};
    		$scope.row.coverage = {};
    	}

    	$scope.manageScenario = function(){
    		angular.forEach($scope.progsetsOptimized, function(val){
	    		$scope.budget[val.short_name] = [];
	    		$scope.coverage[val.short_name] = [];
	    	});
    		
    		var row = {
    			"scenario_type": scenario.scenario_type, 
    			"name": $scope.row.name, 
    			"parset_id": $scope.row.parset_id || null,
    			"active": true, 
    			"pars": [], 
    			"t": [], 
    			"id": scenario.id || null, 
    			"progset_id": $scope.row.progset_id || null
    		};

    		row[$scope.radio] = $scope[$scope.radio];

    		angular.forEach($scope.row.pars, function(val, key){
    			row.t.push(val.year);
				angular.forEach(val, function(v, k){
					if(k !== 'year'){
						row[$scope.radio][k].push(v);
					}
				});
    		});

    		//console.log(JSON.stringify(row));
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
