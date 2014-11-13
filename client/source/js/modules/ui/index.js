define([
  'angular',
  './button-choicebox/index',
  './menu/index',
  '../common/active-project-service',
  '../user-manager/index'
], function (angular) {
  'use strict';

  return angular.module('app.ui', [
    'app.active-project',
    'app.ui.button-choicebox',
    'app.ui.menu'
  ])

    .controller('MainCtrl', function ($scope, $upload, activeProject, UserManager) {

      $scope.user = UserManager.data;
      $scope.userLogged = function () {
        return UserManager.isLoggedIn;
      };
      $scope.logout = UserManager.logout;

      $scope.activeProject = activeProject;

      $scope.asideMenuSettings = {
        items: [
          {
            title: 'Create/open project',
            id: 'create-load',
            subitems: [
              {
                title: 'Create new project',
                state: {
                  name: 'project.create'
                }
              },
              {
                title: 'Open existing project',
                state: {
                  name: 'project.open'
                }
              },
              {
                title: 'Upload Optima spreadsheet',
                click: function () {
                  angular
                    .element('<input type="file">')
                    .change(function (event) {
                      uploadDataSpreadsheet(event.target.files[0]);
                    })
                    .click();
                }
              }
            ]
          },
          {
            title: 'View & calibrate model',
            id: 'create-load',
            subitems: [
              {
                title: 'View data & model calibration',
                state: {
                  name: 'model.view'
                }
              },
              {
                title: 'Define cost-coverage-outcome assumptions',
                state: {
                  name: 'model.define-cost-coverage-outcome'
                }
              }
            ]
          },
          {
            title: 'Analysis',
            subitems: [
              {
                title: 'Scenario analyses',
                state: {
                  name: 'analysis.scenarios'
                }
              },
              {
                title: 'Optimization analyses',
                state: {
                  name: 'analysis.optimization'
                }
              }
            ]
          }
        ]
      };

      // https://github.com/danialfarid/angular-file-upload
      function uploadDataSpreadsheet(file) {
        $scope.upload = $upload.upload({
          url: '/api/project/update',
          file: file
        }).progress(function (evt) {
          console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
        }).success(function (data, status, headers, config) {
          alert('Data spreadsheet was successfully uploaded. For now you can only check that in the console')
          console.log(data);
        });
      }

    });
});
