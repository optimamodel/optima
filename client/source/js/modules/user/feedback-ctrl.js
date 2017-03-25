define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.feedback', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('feedback', {
          url: '/feedback',
          templateUrl: 'js/modules/user/feedback.html'
        });
    });

});
