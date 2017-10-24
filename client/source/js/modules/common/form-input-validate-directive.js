define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.form-input-validate', [])

    .directive('formInputValidate', function () {

      return {
        restrict: 'C',
        require: '^form',
        link: function (scope, el, attrs, formCtrl) {
          // find the text box element, which has the 'name' attribute
          var inputEl = el[0].querySelector('[name]');
          // convert the native text box element to an angular element
          var inputNgEl = angular.element(inputEl);
          // get the name on the text box so we know the property to check on the form controller
          var inputName = inputNgEl.attr('name');

          // only show hints after user clicks submit
          var initialized = false;

          // only apply the has-error class after the user leaves the text box
          inputNgEl.bind('input', function () {
            if (initialized) {
              el.toggleClass('invalid', formCtrl[inputName].$invalid);
              el.toggleClass('valid', formCtrl[inputName].$valid);
            }
          });

          scope.$on('form-input-check-validity', function () {
            initialized = true;
            el.toggleClass('invalid', formCtrl[inputName].$invalid);
            el.toggleClass('valid', formCtrl[inputName].$valid);
          });
        }
      };

    });
});

