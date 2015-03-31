define([
  'angular',
  'jquery',
  'underscore',
  'angular-mocks',
  'Source/modules/ui/menu/menu-directive'
], function (angular, $, _) {
  'use strict';

  describe('menu directive', function () {
    var scope, location, parentScope;
    var $stateSpy = jasmine.createSpyObj('$state', ['href', 'get']);

    beforeEach(module('app.ui.menu'));

    beforeEach(module(function ($provide) {
      $provide.value('$state', $stateSpy);
      $provide.value('security', {});
      $provide.value('typeSelector', {});
    }));

    beforeEach(inject(function ($rootScope, $compile, $location, $httpBackend) {
      $httpBackend.when('GET', 'js/modules/ui/menu/menu-dropdown.tpl.html').respond('<div></div>');

      location = $location;
      $('body').append('<div id="menu" data-menu="settings"></div>');

      // compile and digest
      var elem = angular.element('#menu');
      parentScope = $rootScope.$new();
      parentScope.settings = {
        baseClass: '',
        items: []
      };

      $compile(elem)(parentScope);
      $httpBackend.flush();
      parentScope.$digest();
      scope = elem.isolateScope();
    }));

    describe('_getItemChecker()', function () {
      var items;

      beforeEach(function () {
        items = [
          {
            matchingState: 'calendar'
          },
          {
            state: {
              name: 'dashboard.main'
            }
          },
          {
            matchingState: 'market',
            parent: {}
          }
        ];
      });

      it('should return a curried function', function () {
        expect(scope._getItemChecker('test')).toEqual(jasmine.any(Function));
      });

      it('should make item active when toState.name is matchingState', function () {
        var item = items[0];
        scope._getItemChecker({name: 'calendar'})(item);
        expect(item.active).toBe(true);
      });

      it('should make item active when toState.name contains matchingState', function () {
        var item = items[0];
        scope._getItemChecker({name: 'calendar.regular'})(item);
        expect(item.active).toBe(true);
      });

      it('should NOT make item active when toState.name doesn\'t contain matchingState', function () {
        var item = items[0];
        scope._getItemChecker({name: 'NOTcalendar.regular'})(item);
        expect(item.active).toBe(false);
      });

      it('should make item active when its state equals to toState.name', function () {
        var item = items[1];
        scope._getItemChecker({name: 'dashboard.main'})(item);
        expect(item.active).toBe(true);
      });

      it('should NOT make item active when its state doesn\'t equal to toState.name', function () {
        var item = items[1];
        scope._getItemChecker({name: 'NOTdashboard.main'})(item);
        expect(item.active).toBe(false);
      });

      it('should make item inactive if it has no matchingState or state', function () {
        var item = {};
        scope._getItemChecker({name: 'dashboard.main'})(item);
        expect(item.active).toBe(false);
      });

      it('should make parent active if item is active itself', function () {
        var item = items[2];
        scope._getItemChecker({name: 'market'})(item);
        expect(item.parent.active).toBe(true);
      });

    });

    describe('_processItems()', function () {
      var items;

      beforeEach(function () {
        items = [
          {
            title: 'Dashboard',
            state: {
              name: 'dashboard.main',
              params: {
                bla: 'foo'
              }
            }
          },
          {
            title: 'Market',
            subitems: [
              {
                title: 'Sub-market'
              }
            ]
          }
        ];

        $stateSpy.get.andReturn({ permissions: ['role1', 'role2'] });
        scope._processItems(items);
      });

      // it('should flatten items', function () {
      //   expect(scope._processedItems.length).toBe(3);
      // });
      //
      // it('should flatten items and subitems', function () {
      //   expect(scope._processedItems.length).toBe(3);
      // });
      //
      // it('should create a reference to parent in subitem', function () {
      //   var parentRef = _(scope._processedItems).findWhere({ title: 'Sub-market' }).parent;
      //   expect(parentRef).toBeDefined();
      //   expect(parentRef.title).toBe('Market');
      // });
      //
      // it('should create url from state when its present', inject(function ($state) {
      //   expect($state.href).toHaveBeenCalledWith('dashboard.main', {bla: 'foo'});
      // }));
      //
      // it('should use # as url when no state set', function () {
      //   expect(_(scope._processedItems).findWhere({ title: 'Sub-market' }).url).toBe('#');
      // });

    });

  });
});
