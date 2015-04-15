define([
  './module'
], function (module) {
  'use strict';
  module.controller('GraphsController', function ($scope, mocks) {
    // Lines
    // =======
    $scope.options5 = mocks.data.lineScatter.options;
    $scope.data5 = mocks.data.lineScatter.data;

    // Line + Area
    // =======
    $scope.options6 = mocks.data.lineAreaScatter.options;
    $scope.data6 = mocks.data.lineAreaScatter.data;

    // Stacked Chart
    // =======
    $scope.options7 = mocks.data.stackedChart.options;
    $scope.data7 = mocks.data.stackedChart.data;

    // Pie Chart
    // =======
    $scope.options8 = mocks.data.pieChart.options;
    $scope.data8 = mocks.data.pieChart.data;

    // Stacked bar chart
    // =======
    $scope.options9 = mocks.data.stackedBarChart.options;
    $scope.data9 = mocks.data.stackedBarChart.data;

    // Two sided horizontal bar chart
    // =======
    $scope.options10 = mocks.data.twoSidedHorizontalChart.options;
    $scope.data10 = mocks.data.twoSidedHorizontalChart.data;

    // Radar Chart
    // =======
    $scope.radarOptions = mocks.data.radarChart.options;
    $scope.radarData = mocks.data.radarChart.data;
  });
});
