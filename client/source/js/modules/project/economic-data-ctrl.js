define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectEconomicDataController',
    function ($scope, projects, modalService, $upload, $state, info, projectApiService, $modal) {
      var activeProjectInfo = info.data;
      $scope.hasEconData = activeProjectInfo.has_econ;

      if (!activeProjectInfo.has_data) {
        modalService.inform(
          function (){ },
          'Okay',
          'Please upload spreadsheet to proceed.',
          'Cannot proceed'
        );
        $scope.missingData = true;
        return;
      }

      $scope.economicData = function(action){
        switch(action){
          case 'create':
            projectApiService.getEconomicsData(activeProjectInfo.id)
            .success(function (response, status, headers, config) {
              var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
              saveAs(blob, (activeProjectInfo.name + '_economics.xlsx'));
            });
          break;
          case 'upload':
            var modalInstance = $modal.open({
              templateUrl: 'economicDataUpload.html',
              size: 'sm',
              controller: 'EconomicModalInstanceCtrl',
              resolve: {
                activeProjectInfo: function(){
                  return activeProjectInfo;
                }
              }
            });
            modalInstance.result.then(function (selectedItem) {
              $scope.selected = selectedItem;
            });
          break;
          case 'remove':
            if(!angular.isDefined(activeProjectInfo.econ)){ // Economic data exist
              // Modal and http call to save project
              var message = 'Are you sure want to remove economic data template?';
              modalService.confirm(
                function (){ 
                  projectApiService.deteleEconomicsData(activeProjectInfo.id).then(function(response){
                    $scope.hasEconData = false;
                  });
                },
                function (){},
                'Yes',
                'No',
                message,
                'Economic data'
              );
            }else{ // No economic data found
              modalService.inform(
                function (){ },
                'Okay',
                'No economic data has been uploaded.',
                'Cannot proceed'
              );
            }
          break;
        }
      };
      ////
    })
    .controller('EconomicModalInstanceCtrl',
    function ($scope, activeProjectInfo, $upload) {
      var uploadedFile;
      $scope.onFileSelect = function(files) {
        uploadedFile = files[0];
      };
      $scope.UploadEconomicData = function() {
          var fileName = uploadedFile.name;
          var fileExt = fileName.substr(fileName.lastIndexOf('.') + 1, fileName.length);
          if (fileExt !== 'xlsx') {
            modalService.informError([{message: 'Please upload an excel file. This should have the file extension .xlsx.'}]);
            return false;
          } else {
            $upload.upload({
              url: '/api/project/'+activeProjectInfo.id+'/economics',
              file: uploadedFile
            }).success(function(){
              window.location.reload();
            });
          }
      };

    });
});
