define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.contact', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('contact', {
          url: '/contact',
          templateUrl: 'js/modules/contact/contact.html'
        });
    });

});
