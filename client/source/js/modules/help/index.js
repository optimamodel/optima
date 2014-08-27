define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.help', ['ui.router'])
    .config(['$stateProvider', function ($stateProvider) {
      $stateProvider
        .state('help', {
          url: '/help',
          templateUrl: 'js/modules/help/help.html'
        });
    }]);

});
