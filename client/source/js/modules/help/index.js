define(['angular', '../../version', 'ui.router'], function (angular, version) {
  'use strict';

  return angular.module('app.help', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('help', {
          url: '/help',
          templateUrl: 'js/modules/help/help.html',
          controller: ['$scope', function ($scope) {
            $scope.version = version;
          }]
        });
    });

});
