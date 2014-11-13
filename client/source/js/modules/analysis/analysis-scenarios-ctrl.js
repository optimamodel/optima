define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $modal) {

        $scope.projectParams = {
            name: ''
        };

        $scope.scenarios = [
            { name: 'Conditions remain according to model calibration', active: true }
        ];


        $scope.openAddScenarioModal = function ($event) {
            if ($event) {
                $event.preventDefault();
            }

            return $modal.open({
                templateUrl: 'js/modules/analysis/analysis-scenarios-modal.html',
                controller: 'AnalysisScenariosModalController',
                resolve: {
                    scenario: function () {
                        return {
                            sex: 'male'
                        };
                    }
                }
            }).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    $scope.scenarios.push(newscenario);
                });
        };

        $scope.openEditScenarioModal = function ($event, scenario) {
            if ($event) {
                $event.preventDefault();
            }

            return $modal.open({
                templateUrl: 'js/modules/analysis/analysis-scenarios-modal.html',
                controller: 'AnalysisScenariosModalController',
                resolve: {
                    scenario: function () {
                        return scenario;
                    }
                }
            }).result.then(
                function (newscenario) {
                    scenario.active = true;
                    _(scenario).extend(newscenario);
                });
        };



        var toCleanArray = function (collection) {
            return _(collection).chain()
                .where({ active: true })
                .map(function (item) {
                    return _(item).omit(['active', '$$hashKey'])
                })
                .value();
        };

    });

});