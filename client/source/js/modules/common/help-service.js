define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.open-help', [])
    .factory('helpService', [
      '$modal', 'url',
      function ($modal, url) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
      }]);
});