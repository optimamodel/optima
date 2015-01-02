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

    .controller('MainCtrl', function ($window, $scope, $upload, $state, activeProject, UserManager, modalService) {

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
                  if (activeProject.isSet()) {
                  angular
                    .element('<input type="file">')
                    .change(function (event) {
                      uploadDataSpreadsheet(event.target.files[0]);
                    })
                    .click();
                  } else {
                      modalService.inform(
                        function (){ },
                        'Okay',
                        'Create or open a project first.',
                        'Cannot proceed'
                      );
                  }
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
                click: function() {
                  ifActiveProject($state, 'model.view', activeProject);
                },
              },
              {
                title: 'Define cost-coverage-outcome assumptions',
                click: function() {
                  ifActiveProject($state, 'model.define-cost-coverage-outcome', activeProject);
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
                click: function() {
                  ifActiveProject($state, 'analysis.scenarios', activeProject);
                }
              },
              {
                title: 'Optimization analyses',
                click: function() {
                  ifActiveProject($state, 'analysis.optimization', activeProject);
                }
              }
            ]
          }
        ]
      };

      function ifActiveProject(state, name, activeProject) {
        if(activeProject.isSet()){
          state.go(name);
        } else {
            modalService.inform(
              function (){ },
              'Okay',
              'Create or open a project first.',
              'Cannot proceed'
            );
         }
      }

      // http://stackoverflow.com/a/9407953/829533
      // service to call uploadDataSpreadsheet from calibration-ctrl.js
      $scope.$on('uploadDataSpreadsheet', function(event, args) {
        uploadDataSpreadsheet(args.file);
      });
      
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
                function (){ 
                  // reload the page after upload.
                  window.location.reload();
                },
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
