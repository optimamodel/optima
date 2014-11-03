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
          url: '/api/project/update',
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
                            title: 'View data & model estimates',
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
                    title: 'Forecasts & counterfactuals',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'Manage counterfactuals',
                            state: {
                                name: 'forecasts.counterfactuals'
                            }
                        },
                        {
                            title: 'View results',
                            state: {
                                name: 'forecasts.results'
                            }
                        }
                    ]
                },
                {
                    title: 'Analysis & optimization',
                    id: 'create-load',
                    subitems: [
                        {
                            title: 'Define optimization objectives',
                            state: {
                                name: 'optimization.objectives'
                            }
                        },
                        {
                            title: 'Define optimization constraints',
                            state: {
                                name: 'optimization.constraints'
                            }
                        },
                        {
                            title: 'Run optimization',
                            state: {
                                name: 'optimization.optimize'
                            }
                        },
                        {
                            title: 'View results',
                            state: {
                                name: 'optimization.results'
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
