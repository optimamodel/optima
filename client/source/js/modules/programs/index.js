define(
  ['angular', 'ui.router', './program-set-ctrl', './program-modal-ctrl'],
  function (angular) {

  'use strict';

  var module = angular.module(
    'app.programs',
    ['ui.router', 'app.program.modal', 'app.programs.ctrl']);

  module.config(function($stateProvider) {
    $stateProvider
      .state('programs', {
        url: '/programs',
        templateUrl: 'js/modules/programs/program-set.html',
        controller: 'ProgramSetController'
      });
  });
});
