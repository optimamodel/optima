/**
 *  A service to upload files
 */

define([
  'angular'
  ], function (angular) {
  'use strict';

  return angular.module('app.common.file-upload',[])
  .factory(
    'fileUpload',
    [
      '$http', '$upload', 'modalService', 'activeProject', 'projectApiService',
      function ($http, $upload, modalService, activeProject, projectApiService) {

        var uploadDataSpreadsheet = function(scope, file, url, reload) {
          if (url === undefined) {
            var projectId = activeProject.getProjectIdForCurrentUser();
            url = projectApiService.getSpreadsheetUrl(projectId);
          }
          if (reload === undefined ) {
            reload = true;
          }
          scope.upload = $upload.upload({
            url: url,
            file: file
          });

          console.log('activeProject', activeProject);

          scope.upload.success(function (response) {
            modalService.inform(
              function (){
                // reload the page after upload.
                if (reload) window.location.reload();
              },
              'Okay',
              response,
              'Upload completed'
            );
          });
        };
        return {
          uploadDataSpreadsheet: uploadDataSpreadsheet
        };
      }
    ]
  );
});
