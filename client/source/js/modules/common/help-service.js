define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])

    .factory('helpService', ['$modal', function($modal) {

      //function openHelp(helpURL) {
      //  return $modal.open({
      //    templateUrl: 'js/modules/common/help-modal.html',
      //    size: 'lg'
      //  });
      //}

      function openHelp(helpURL) {
        newwindow = window.open(helpURL,'name','height=80%,width=80%');
        if (window.focus) {newwindow.focus()}
        return false;
      }

      return {openHelp: openHelp};
    }]);
});
