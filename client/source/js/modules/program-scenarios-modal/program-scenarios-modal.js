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

      $scope.row.t = [];
      $scope.row.budget = [];
      _.forEach($scope.progsetsOptimized, function(progset) {
        $scope.row.budget.push(
          {'program':progset.short_name, 'values':[]}
        );
      });

      $scope.manageScenario = function(){
    		var row = {
    			"scenario_type": $scope.row.scenario_type,
    			"name": $scope.row.name, 
    			"parset_id": $scope.row.parset_id || null,
    			"active": true, 
    			"t": $scope.row.t,
          "budget": $scope.row.budget,
    			"id": $scope.row.id || null, 
    			"progset_id": $scope.row.progset_id || null
    		};
    		$modalInstance.close(row);
    	};

        $scope.addParam = function(row) {
          if (!$scope.temp) {
            $scope.temp = [];
            }
          $scope.temp.push({});
        };

        $scope.removeParam = function(row, paramIndex) {
            row.pars = _.reject(row.pars, function (param, index) {
                return index === paramIndex
            });
        };
    });
});
