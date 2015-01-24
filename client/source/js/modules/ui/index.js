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

    .controller('MainCtrl', function ($window, $scope, $upload, $state, $http, activeProject, UserManager, modalService) {

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
                      uploadData(event.target.files[0], '/api/project/update');
                    })
                    .click();
                  } else {
                    showProjectNotActive();
                  }
                }
              },
              {
                title: 'Download project',
                click: function () {
                  if (activeProject.isSet()) {
                    $http({url:'/api/project/downloadproject/'+ activeProject.name,
                      method:'GET',
                      headers: {'Content-type': 'application/json'},
                      responseType:'arraybuffer'})
                      .success(function (response, status, headers, config) {
                        var blob = new Blob([response], { type: 'application/json' });
                        saveAs(blob, (activeProject.name + '.json'));
                      })
                      .error(function (response) {});
                  } else {
                    showProjectNotActive();
                  }
                }
              },
              {
                title: 'Upload projects',
                click: function () {
                  if (activeProject.isSet()) {
                  angular
                    .element('<input type="file">')
                    .change(function (event) {
                      uploadData(event.target.files[0], '/api/project/uploadproject');
                    })
                    .click();
                  } else {
                    showProjectNotActive();
                  }
                }
              },
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
                state: {
                  name: 'model.view'
                }
              },
              {
                title: 'Define cost-coverage-outcome assumptions',
                click: function() {
                  ifActiveProject($state, 'model.define-cost-coverage-outcome', activeProject);
                },
                state:{
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
                click: function() {
                  ifActiveProject($state, 'analysis.scenarios', activeProject);
                },
                state:{
                  name: 'analysis.scenarios'
                }
              },
              {
                title: 'Optimization analyses',
                click: function() {
                  ifActiveProject($state, 'analysis.optimization', activeProject);
                },
                state:{
                  name: 'analysis.optimization'
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
            showProjectNotActive();
         }
      }

      function showProjectNotActive() {
        modalService.inform(
          function (){ },
          'Okay',
          'Create or open a project first.',
          'Cannot proceed'
        );
      }

      // https://github.com/danialfarid/angular-file-upload
      function uploadData(file, url) {
        $scope.upload = $upload.upload({
          url: url,
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
            alert('Sorry, but server feels bad now. Please, give it some time to recover');
          }

        });
      }

    });
});
