define([
  'angular',
  'ui.router',
  '../../config'
], function (angular) {
  'use strict';

  return angular.module('app.import-export', [
    'app.constants',
    'ui.router'
  ]).config(['$stateProvider', function ($stateProvider) {
    $stateProvider
      .state('import-export', {
        url: '/import-export',
        templateUrl: '/js/modules/import-export/import-export.html',
        controller: 'ImportExportController'
      })
  }]);

});
