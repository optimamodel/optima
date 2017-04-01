define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])

    .factory('helpService', ['$modal', function($modal) {

      function openHelp(helpURL) {
        return $modal.open({
          templateUrl: 'js/modules/common/help-modal.html',
          size: 'lg'
        });
      }

      return {openHelp: openHelp};
    }]);
});
