define(['angular'], function (angular) {
  'use strict';

  /**
   * app.help loads help text with a helpId
   */

  var module = angular.module('app.rpc', []);

  // module.factory('rpc', ['$http', function($http) {
  //   return { runProcedure: runProcedure() };
  // }])

  module.directive('helpMe', function($http) {

    function runRemoteProcedure(name, args, kwargs) {
      return $http.post(
        '/api/procedure',
        { name: name, args, args: args, kwargs: kwargs });
    }

    return {
      template: '<a ng-mouseenter="mouseenter()" ng-mouseleave="mouseleave()">[?]</a>',
      link: function(scope, element, attrs) {
        let div = angular.element('<div style="display: inline"></div>');

        scope.tpl = angular.element(
          '<div style="display: none; position: absolute; font-size: 10px; font-weight: normal; background: white; border: 1px solid #999; padding: 10px; margin-top: 5px; margin-left: -5px"><div class="arrow-down"></div></div>');

        element.append(div);
        div.append(scope.tpl);

        runRemoteProcedure(
            'load_help', [attrs.helpId])
          .then(function(response) {
            scope.tpl.html(response.data.html);
          });

        scope.mouseenter = function() {
          scope.tpl.css('display', 'block');
          scope.tpl.css('left', div.position().left);
          scope.tpl.css('top', div.position().top);
        };

        scope.mouseleave = function() {
          scope.tpl.css('display', 'none');
        };
      }
    };
  });

  return module;

});
