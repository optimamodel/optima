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
        newwindow = window.open('https://docs.google.com/document/d/18hGjBb1GO8cR_sZRTjMqBvBb0Fkmsz-DwzslstaqG-Y/edit?usp=sharing','name','height=200,width=150');
        if (window.focus) {newwindow.focus()}
        return false;
      }

      return {openHelp: openHelp};
    }]);
});
