define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectEconomicDataController',
    function ($scope, projects, modalService, $upload, $state, info, projectApiService, $modal) {
      var activeProjectInfo = info.data;
      
      $scope.economicData = function(action){
        switch(action){
          case 'create':
            /*projectApiService.getProjectData(activeProjectInfo.id)
            .success(function (response, status, headers, config) {
              var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
              saveAs(blob, (activeProjectInfo.name + '.xlsx'));
            });*/
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
              var message = 'Are you sure want to remove economic data?';
              modalService.confirm(
                function (){ 
                  activeProjectInfo.econ = '';
                  projectApiService.updateProject(activeProjectInfo.id, activeProjectInfo);
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
      $scope.onFileSelect = function(files) {
        activeProjectInfo.file = files[0];
      };
      $scope.UploadEconomicData = function() {
          var fileName = activeProjectInfo.file.name;
          var fileExt = fileName.substr(fileName.lastIndexOf('.') + 1, fileName.length);
          if (fileExt !== 'xlsx') {
            modalService.informError([{message: 'Please upload an excel file. This should have the file extension .xlsx.'}]);
            return false;
          } else {
             $upload.upload({
               url: '/api/project/data',
               file: activeProjectInfo.file
             }).success(function (data, status, headers, config) {
              window.location.reload();
            });
          }
      };

    });
});
