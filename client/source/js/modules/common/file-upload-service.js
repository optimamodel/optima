define(['angular'], function (angular) {

  'use strict';

  return angular.module('app.common.file-upload', [])

    /**
     *  Service to upload data spreadsheets to current project
     */

    .factory(
      'fileUpload',
      ['$http', '$upload', 'modalService', 'activeProject', 'projectApiService', '$state',
      function ($http, $upload, modalService, activeProject, projectApiService, $state) {

        return {

          uploadDataSpreadsheet: function(scope, file, url, reload) {

            if (url === undefined) {
              var projectId = activeProject.getProjectIdForCurrentUser();
              url = projectApiService.getSpreadsheetUrl(projectId);
            }

            if (reload === undefined ) { reload = true; }

            scope.upload = $upload
              .upload({url: url, file: file})
              .success(function (response) {
                modalService.inform(
                   function() { if (reload) { $state.reload(); } },
                  'Okay',
                  response,
                  'Upload completed'
                );
              });

          }

        };

    }]);

});
