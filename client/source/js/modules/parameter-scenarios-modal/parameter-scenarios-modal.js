define(['angular'], function (module) {
  'use strict';

  return angular.module('app.parameter-scenarios-modal', [])
    .controller('ParameterScenariosModalController', function ($scope, $modalInstance, modalService, scenario, parsets, progsets, ykeys, openProject) {
    	$scope.row = scenario;
    	$scope.parsets = parsets;
        $scope.progsets = progsets;
        $scope.ykeys = ykeys.data.keys;
    	$scope.openProject = openProject.populations;
    	
    	$scope.params = [];
    	$scope.par = {};
    	$scope.forData = [];
    	
        $scope.parsForSelectedParset = function(row) {
            var parset = _.filter($scope.parsets, {id: row.parset_id});
            if (parset.length > 0) {
                return _.filter(parset[0].pars[0], {visible: 1});
            }
            return [];
        };

        $scope.popsForParam = function(param, row) {
            if ($scope.ykeys.hasOwnProperty(row.parset_id) && $scope.ykeys[row.parset_id].hasOwnProperty(param)) {
                return $scope.ykeys[row.parset_id][param];
            }
            return [];
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
    			"pars": $scope.row.pars, 
    			"id": scenario.id || null, 
    			"progset_id": $scope.row.progset_id || null
    		};

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
