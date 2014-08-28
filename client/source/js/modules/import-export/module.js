define([
  'angular',
  'ui.router',
  '../converter/converter-service'
], function (angular) {
  'use strict';

  return angular.module('app.import-export', [
    'app.converter',
    'ui.router'
  ]).config(function ($stateProvider) {
    $stateProvider
      .state('import-export', {
        url: '/import-export',
        templateUrl: '/js/modules/import-export/import-export.html',
        controller: 'ImportExportController'
      })
  });

});
