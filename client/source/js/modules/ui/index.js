define([
  'angular',
  './button-choicebox/index',
  './menu/index',
  './modal/modal-service',
  '../common/active-project-service',
  '../user-manager/index'
], function (angular) {
  'use strict';

  return angular.module('app.ui', [
    'app.active-project',
    'app.ui.button-choicebox',
    'app.ui.modal',
    'app.ui.menu'
  ])

    .controller('MainCtrl', function ($scope, $upload, activeProject, UserManager, modalService) {

      $scope.user = UserManager.data;
      $scope.userLogged = function () {
        return UserManager.isLoggedIn;
      };

      $scope.activeProject = activeProject;

      $scope.asideMenuSettings = {
        items: [
          {
            title: 'Create/open project',
            id: 'create-load',
            matchingState: 'project',
            subitems: [
              {
                title: 'Create new project',
                state: {
                  name: 'project.create'
                }
              },
              {
                title: 'Open/manage projects',
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
            matchingState: 'model',
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
            matchingState: 'analysis',
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
        }).success(function (data) {
          if (data.status === 'NOK') {
            alert("Something went wrong during an upload.\nSee the error:\n" + data.reason);
          } else if (data.status === 'OK') {

              var message = data.file + " was successfully uploaded.\n" + data.result;
              modalService.inform(
                function (){ console.log('informed!') },
                'Okay',
                message,
                'Upload completed'
              );
          } else {
            alert('Sorry, but server feels bad now. Please, give it some time to recover')
          }

        });
      }

    });
});
