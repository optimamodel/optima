/**
 *  A service to upload files
 */

define([
  'angular'
  ], function (angular) {
  'use strict';

  return angular.module('app.common.file-upload',[])
  .factory('fileUpload', ['$http', '$upload', 'modalService', function ($http, $upload, modalService) {
    var uploadDataSpreadsheet = function(scope, file, url, reload) {
      if (url === undefined) {
        url = '/api/project/update';
      }
      if (reload === undefined ) {
        reload = true;
      }
      scope.upload = $upload.upload({
        url: url,
        file: file
      });

      scope.upload.success(function (data) {
        var message = data.file + " was successfully uploaded.\n" + data.result;
        modalService.inform(
          function (){
            // reload the page after upload.
            if (reload) window.location.reload();
          },
          'Okay',
          message,
          'Upload completed'
        );
      });
    };
    return {
      uploadDataSpreadsheet: uploadDataSpreadsheet
    };
 }]);
});
