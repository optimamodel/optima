define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.open-help', [])
    .controller('helpModalController', function ($modal, helpURL) {
      function openHelp(helpURL) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
      }
    });
});