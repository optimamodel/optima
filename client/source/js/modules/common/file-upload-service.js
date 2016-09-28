/**
 *  Service to upload data spreadsheets to current project
 */

define(['angular'], function (angular) {

  'use strict';

  return angular.module('app.common.file-upload', []).factory(
    'fileUpload',
    [
      '$http', '$upload', 'modalService', 'activeProject', 'projectApiService',
      function ($http, $upload, modalService, activeProject, projectApiService) {
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
                   function() { if (reload) { window.location.reload(); } },
                  'Okay',
                  response,
                  'Upload completed'
                );
              });

          }
        };
      }
    ]
  );

});
