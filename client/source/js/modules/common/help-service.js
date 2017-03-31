define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.open-help', [])
    .factory('openHelp', [
      '$modal', 'url',
      function ($modal, url) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
      }]);
});