define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $modal) {

        $scope.projectParams = {
            name: ''
        };

        $scope.scenarios = [
            { name: 'Female sex workers', acronym: 'FSW', active: false },
            { name: 'Clients of sex workers', acronym: 'CSW', active: false },
            { name: 'Men who have sex with men', acronym: 'MSM', active: false },
            { name: 'People who inject drugs', acronym: 'PWID', active: false },
            { name: 'Males who inject drugs', acronym: 'MWID', active: false },
            { name: 'Females who inject drugs', acronym: 'FWID', active: false },
            { name: 'Transgender individuals', acronym: 'TG', active: false },
            { name: 'Children (2-15)', acronym: 'CHLD', active: false },
            { name: 'Infants (0-2)', acronym: 'INF', active: false },
            { name: 'Other males (15-49)', acronym: 'OM15-49', active: false },
            { name: 'Other females (15-49)', acronym: 'OF15-49', active: false },
            { name: 'Other males [enter age]', acronym: 'OM', active: false },
            { name: 'Other females [enter age]', acronym: 'OF', active: false }
        ];


        $scope.openAddScenarioModal = function ($event) {
            if ($event) {
                $event.preventDefault();
            }

            return $modal.open({
                templateUrl: 'js/modules/project/analysis-scenarios-modal.html',
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
                templateUrl: 'js/modules/project/analysis-scenarios-modal.html',
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