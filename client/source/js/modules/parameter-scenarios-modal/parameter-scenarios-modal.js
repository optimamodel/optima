define(['angular'], function (module) {
  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function ($scope, $modalInstance, modalService, scenario, parsets, openProject) {
    	$scope.row = scenario;
    	$scope.parsets = parsets.data.parsets;
    	$scope.openProject = openProject.populations;
    	
    	$scope.params = [];
    	$scope.par = {};
    	$scope.forData = [];
    	
    	console.log(scenario, parsets.data.parsets);

    	$scope.manageParameters = function(){
    		$scope.par.name = $scope.par.name['name'];
    		console.log('Param', $scope.par);
    		$scope.params.push($scope.par);
    	};

    	$scope.populateForData = function(data){
    		$scope.forData = JSON.parse(data);
    	};

    	$scope.manageScenario = function(){
    		var row = {
    			"scenario_type": scenario.scenario_type, 
    			"name": $scope.row.name, 
    			"parset_id": $scope.row.parset_id || null,
    			"active": true, 
    			"pars": $scope.params, 
    			"id": scenario.id || null, 
    			"progset_id": $scope.row.progset_id
    		};

    		/*var pRow = {
				"name": "circum", 
				"startyear": 2000, 
				"for": ["M 15-49"], 
				"endval": 1, 
				"endyear": 2020, 
				"startval": 1
			};*/
    		//row["pars"].push(pRow);

    		console.log(row);
    	}

    });
});
