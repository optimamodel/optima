define([
  './module',
  'underscore'
], function (module, _) {
  'use strict';

  module.controller('ImportExportController', ['$scope', '$timeout', 'converter', function ($scope, $timeout, converter) {
    /**
     * Init models
     */

    $scope.json = [
      ['', '2009', '2010', '2011', '2012', '2013'],
      [
        ['TRU', 25, 34, 55, 2, 1],
        ['MIN', 25, 34, 55, 2, 1],
        ['TRU', 25, 2, 55, 2, 1],
        ['WAD', 25, 34, 55, 2, 1],
        ['TRU', 25, 5, 55, 2, 1],
        ['GRE', 2, 77, 55, 2, 1]
      ]
    ];

    $scope.export2cvs = function () {
      converter.json2cvs($scope.json).download();
    };

    $scope.export2xlsx = function () {
      converter.json2xlsx('mockup-table').download();
    };

  }]);
});
