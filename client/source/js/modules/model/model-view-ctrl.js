define(['./module'], function (module) {
    'use strict';

    module.controller('ModelViewController', function ($scope) {

        $scope.scatteroptions = {
            chart: {
                type: 'scatterChart',
                height: 450,
                margin: {
                    top: 20,
                    right: 20,
                    bottom: 60,
                    left: 40
                },
                x: function (d) {
                    return d[0];
                },
                y: function (d) {
                    return d[1];
                },
                clipEdge: true,
                transitionDuration: 500,
                useInteractiveGuideline: true,
                xAxis: {
                    showMaxMin: false,
                    ticks: 9,
                    tickFormat: function (d, i) {
                        return ['Parameter 1', 'Parameter 2', 'Parameter 3', 'Parameter 4', 'Parameter 5', 'Parameter 6', 'Parameter 7', 'Parameter 8', 'Parameter 9'][d];
                    }
                },
                yAxis: {
                    tickFormat: function (d) {
                        return d3.format(',.2f')(d);
                    }
                }
            }
        };

        $scope.scatterdata = [
            {
                "key": "Model",
                "values": [
                    [1, 0.200],
                    [2, 1.199],
                    [3, 2.198],
                    [4, 3.198],
                    [5, 0.198],
                    [6, 4.198],
                    [7, 3.198],
                    [8, 2.595],
                    [9, 1.195]
                ]
            },

            {
                "key": "Data",
                "values": [
                    [1, 0.200],
                    [2, 1.599],
                    [3, 2.298],
                    [4, 3.798],
                    [5, 0.898],
                    [6, 4.298],
                    [7, 3.598],
                    [8, 2.295],
                    [9, 1.895]
                ]
            }

        ];
    });
});
