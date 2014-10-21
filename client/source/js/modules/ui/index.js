define([
    'angular',
    './button-choicebox/index',
    './menu/index'
], function (angular) {
    'use strict';

    return angular.module('app.ui', [
        'app.ui.button-choicebox',
        'app.ui.menu'
    ]).controller('MainCtrl', function ($scope, $upload) {

      // https://github.com/danialfarid/angular-file-upload
      function uploadDataSpreadsheet(file) {
        $scope.upload = $upload.upload({
          url: '/api/data/upload',
          file: file
        }).progress(function(evt) {
          console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
        }).success(function(data, status, headers, config) {
          alert('Data spreadsheet was successfully uploaded. For now you can only check that in the console')
          console.log(data);
        });
      }

        $scope.asideMenuSettings = {
            items: [
                {
                    title: 'Home',
                    state: {
                        name: 'home'
                    }
                },
                {
                    title: 'Step 1: Create/open project',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'Create new project',
                            state: {
                                name: 'project.create'
                            }
                        },
                        {
                            title: 'Upload data spreadsheet',
                            click: function () {
                                angular
                                  .element('<input type="file">')
                                  .change(function (event) {
                                    uploadDataSpreadsheet(event.target.files[0]);
                                  })
                                  .click();
                            }
                        },
                        {
                            title: 'Open existing project',
                            click: function () {
                                angular
                                  .element('<input type="file">')
                                  .change(function (event) {
                                      // TODO
                                      alert(event.target.files[0].name);
                                  })
                                  .click();
                            }
                        }
                    ]
                },
                {
                    title: 'Step 2: View & calibrate model',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'View model & data',
                            state: {
                                name: 'model.view'
                            }
                        },
                        {
                            title: 'Automatic calibration',
                            state: {
                                name: 'model.automatic-calibration'
                            }
                        },
                        {
                            title: 'Manual calibration',
                            state: {
                                name: 'model.manual-calibration'
                            }
                        }
                    ]
                },
                {
                    title: 'Step 3: Analysis',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'Define objectives',
                            state: {
                                name: 'optimization.objectives'
                            }
                        },
                        {
                            title: 'Define constraints',
                            state: {
                                name: 'optimization.constraints'
                            }
                        },
                        {
                            title: 'Run analysis',
                            state: {
                                name: 'optimization.optimize'
                            }
                        }
                    ]
                },
                {
                    title: 'Step 4: View/output results',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'Epidemiological results',
                            state: {
                                name: 'results.epiresults'
                            }
                        },
                        {
                            title: 'Economic results',
                            state: {
                                name: 'results.econresults'
                            }
                        }
                    ]
                }
            ]
        };

        $scope.exitApp = function () {
            window.close();
        }
    });
});
