define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.global-pollster', [])

    .factory('tmpHelpService', ['$modal', function($modal) {

      function openHelp(helpURL) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
      }

      return {
        openHelp: openHelp
      };

    }]);

});
