define(['angular', 'ui.router'], function (angular) {
  'use strict';

  return angular.module('app.about', ['ui.router'])
    .config(function ($stateProvider) {
      $stateProvider
        .state('about', {
          url: '/about',
          templateUrl: 'js/modules/about/about.html'
        });
    });

});
