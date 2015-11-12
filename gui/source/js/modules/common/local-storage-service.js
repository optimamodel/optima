define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.local-storage', [])

    .provider('localStorage', function () {

      // Polyfill

      /**
       * @ NAME: Cross-browser TextStorage
       * @ DESC: text storage solution for your pages
       * @ COPY: sofish, http://sofish.de
       */
      typeof window.localStorage == 'undefined' && ~function () {

        var localStorage = window.localStorage = {},
          prefix = 'data-userdata',
          doc = document,
          attrSrc = doc.body,

        // save attributeNames to <body>'s `data-userdata` attribute
          mark = function (key, isRemove, temp, reg) {

            attrSrc.load(prefix);
            temp = attrSrc.getAttribute(prefix) || '';
            reg = new RegExp('\\b' + key + '\\b,?', 'i');

            var hasKey = reg.test(temp) ? 1 : 0;

            temp = isRemove ? temp.replace(reg, '') : hasKey ? temp : temp === '' ? key : temp.split(',').concat(key).join(',');

            alert(temp);

            attrSrc.setAttribute(prefix, temp);
            attrSrc.save(prefix);

          };

        // add IE behavior support
        attrSrc.addBehavior('#default#userData');

        localStorage.getItem = function (key) {
          attrSrc.load(key);
          return attrSrc.getAttribute(key);
        };

        localStorage.setItem = function (key, value) {
          attrSrc.setAttribute(key, value);
          attrSrc.save(key);
          mark(key);
        };

        localStorage.removeItem = function (key) {
          attrSrc.removeAttribute(key);
          attrSrc.save(key);
          mark(key, 1);
        };

        // clear all attributes on <body> tag that using for textStorage
        // and clearing them from the
        // 'data-userdata' attribute's value of <body> tag
        localStorage.clear = function () {

          attrSrc.load(prefix);

          var attrs = attrSrc.getAttribute(prefix).split(','),
            len = attrs.length;

          if (attrs[0] === '') return;

          for (var i = 0; i < len; i++) {
            attrSrc.removeAttribute(attrs[i]);
            attrSrc.save(attrs[i]);
          }

          attrSrc.setAttribute(prefix, '');
          attrSrc.save(prefix);

        };

      }();

      this.$get = function () {
        return window.localStorage;
      };
    });

});
