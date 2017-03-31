define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.common.open-help-modal', [])

    .directive('openHelpModal', function (url) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
    });
});