define([
  'angular',
  './button-choicebox/index',
  './menu/index'
], function (angular) {
  'use strict';

  return angular.module('app.ui', [
    'app.ui.button-choicebox',
    'app.ui.menu'
  ]).controller('MainCtrl', function ($scope) {
    $scope.asideMenuSettings = {
      items: [
        {
          title: 'Create/load project',
          id: 'create-load',
          subitems: [
            {
              title: 'Create new project',
              id: 'createNew',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Upload data spreadsheet',
              id: 'createNew',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Load existing project',
              id: 'createNew',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Modify existing project',
              id: 'createNew',
              state: {
                name: 'graphs'
              }
            }
          ]
        },
        {
          title: 'View & calibrate model',
          id: 'create-load',
          subitems: [
            {
              title: 'View model & data',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Automatic calibration',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Manual calibration',
              state: {
                name: 'graphs'
              }
            }
          ]
        },
        {
          title: 'Optimization',
          id: 'create-load',
          subitems: [
            {
              title: 'Define objectives',
              state: {
                name: 'graphs'
              }
            },
            {
              title: 'Define constraints',
              state: {
                name: 'graphs'
              }
            }
          ]
        },
        {
          title: 'View/output results',
          id: 'create-load'
        }
      ]
    };

  });
});
