//define(['angular'], function (angular) {
//  'use strict';
//
//  return angular.module('app.open-help', [])
//    .controller('helpModalController', function ($modal, helpURL) {
//      function openHelp(helpURL) {
//        return $modal.open({
//          templateUrl: 'js/modules/programs/program-set/program-modal.html',
//          size: 'lg'
//        });
//      }
//    });
//});


define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])
    .factory('helpService', ['$modal', 'helpURL',
      function ($modal, helpURL) {

        function openHelp(helpURL) {

          return $modal.open({
            templateUrl: 'js/modules/programs/program-set/program-modal.html',
            size: 'lg'
          });
        }
      }
    ])
});
