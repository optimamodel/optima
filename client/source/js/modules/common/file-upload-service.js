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
      }).success(function (data) {
        if (data.status === 'NOK') {
          alert("Something went wrong during an upload.\nSee the error:\n" + data.reason);
        } else if (data.status === 'OK') {
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
        } else {
          modalService.inform(undefined,undefined,'Sorry, but server feels bad now. Please, give it some time to recover');
        }
      });
    };
    return {
      uploadDataSpreadsheet: uploadDataSpreadsheet
    };
 }]);
});