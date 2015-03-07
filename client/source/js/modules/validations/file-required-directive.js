define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.validations.file-required', [])
    .directive('fileRequired',function(){
      return {
        require:'ngModel',
        link:function(scope,el,attrs,ctrl) {

          ctrl.$setValidity('fileRequired', el.val());

          // change event is fired when file is selected
          el.bind('change',function(){
            scope.$apply(function(){
              ctrl.$setValidity('fileRequired', el.val());
            });
          });
        }
      };
  });
});
