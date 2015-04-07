define(['./module'], function (module) {
  /**
   * Adds a gridster-item directive to the element.
   *
   * See resizable-chart-panel-directive.js.
   */
  return module
      .directive('resizableChart', function () {
        return {
          template: '<div gridster-item="item.gridsterItem" ng-transclude></div>',
          transclude: true,
          replace: true,
          restrict: 'A',
          scope: {
            item: "=resizableChart"
          },
          link: function (scope, element) {
          }
        }
      });
});
