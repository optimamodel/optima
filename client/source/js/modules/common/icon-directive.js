define(['angular' ], function (angular) {
  'use strict';

  var module = angular.module('app.icon-directive', []);

  // <help ref="section-marker">

  function openHelp(helpKey) {

    // Define mapping between help buttons and headings in the user manual
    var baseURL = "https://docs.google.com/document/d/18hGjBb1GO8cR_sZRTjMqBvBb0Fkmsz-DwzslstaqG-Y/edit#heading=";
    var headingMap = {"create-projects":"h.r0x9aoct97nw",
      "manage-projects":"h.v0igq6vp8yvu",
      "create-new-project":"h.a7h2uof7zeek",
      "manage-populations":"h.vn479lpgxo0t",
      "create-data-spreadsheet":"h.mjo0bfk4x6gq",
      "parameter-sets":"h.hrrksxxt32ey",
      "calibration-panel":"h.f3jzk6oecqd9",
      "art-projection-assumptions":"h.7z3p47ssauik",
      "automatic-calibration":"h.x9hisc2lxnln",
      "manual-calibration":"h.da77fbanyz1n",
      "export-single-figure":"h.mxtp4gq0xbw",
      "program-sets":"h.3qlnrs1yi6px",
      "programs":"h.9zw6hj7anqs8",
      "define-cost-function":"h.qysepvi5gw7q",
      "spending-and-coverage":"h.h8964flab3py",
      "define-outcome-functions":"h.a646623wsrlk",
      "most-recent-budget":"h.vg2tyznk9be8",
      "program-parameters":"h.ny54thszrqfz",
      "programs-target-populations":"h.onrq0vaurdf7",
      "programs-target-parameters":"h.16noy3t5d8y1",
      "parameter-scenarios":"h.evz19slwafdv",
      "budget-scenarios":"h.y0o3p8cllolj",
      "coverage-scenarios":"h.ykvgsk15142k",
      "viewing-scenarios":"h.syuxr0k2n3yy",
      "outcomes-optimization":"h.o37t30hyy3kk",
      "optimization-set-objectives":"h.6z5lop6dgufy",
      "optimization-set-constraints":"h.5tac44qso8uz",
      "optimization-set-money-objectives":"h.obw56p83a4ju",
      "money-optimization":"h.87lvxvm6jlmn",
      "viewing-optimizations":"h.1etk4nni7qqi",
      "portfolios":"h.pyvxrvk3b1wm",
      "create-regions":"h.dcny60dj9uqe",
      "adding-regions":"h.doxm4q6evo40",
      "running-geo-analyses":"h.2twkzg2guckm",
      "running-budget-objective-curves":"h.ulc254ll3tnd",
      "running-geospatial-analysis":"h.m0zeriqn6g9q",
      "exporting-geospatial-results":"h.10vjtd9maa2d"};

    var headingURL = headingMap[helpKey];

    var fullURL = baseURL + headingURL;
    console.log('openHelp ', helpKey, fullURL);
    var scrh = screen.height;
    var scrw = screen.width;
    var h = scrh * 0.8; // Height of window
    var w = scrw * 0.6; // Width of window
    var t = scrh * 0.1; // Position from top of screen -- centered
    var l = scrw * 0.37; // Position from left of screen -- almost all the way right
    var newwindow = window.open(fullURL, 'Reference manual', 'width=' + w + ',height=' + h + ',top=' + t + ',left=' + l);
    if (window.focus) {
      newwindow.focus()
    }
    return false;
  }

  module.directive('help', function() {
    return {
      restrict: 'E',
      scope: {
        ref: '@'
      },
      template:
        '<i '
          + 'class="fa fa-question-circle-o"'
          + 'tp-text="Help" tooltip tp-class="tooltip"'
          + 'tp-x="-50" tp-y="-150" tp-anchor-x="0" tp-anchor-y="0"'
          + 'style="margin-left: 0.5em; color: #29abe2; font-size: 14px"'
          + 'ng-click="run()"'
          + '></i>'
        ,
      link: function(scope, elem, attrs) {
        scope.run = function(info) { openHelp(scope.ref); };
      }
    }
  });

  // <icon action="copy" click="someFn()"/>
  module.directive('icon', function($compile) {

    var iconTypes = {
      'copy': { iconName: 'fa-copy', helpText: 'Copy'},
      'new': { iconName: 'fa-file-o', helpText: 'New'},
      'edit': { iconName: 'fa-pencil', helpText: 'Edit'},
      'delete': { iconName: 'fa-trash-o', helpText: 'Delete'},
      'upload': { iconName: 'fa-upload', helpText: 'Upload'},
      'download': { iconName: 'fa-download', helpText: 'Download'},
	    'undo': { iconName: 'fa-undo', helpText: 'Undo'},
	    'redo': { iconName: 'fa-repeat', helpText: 'Redo'},
      'refresh': { iconName: 'fa-sync', helpText: 'Refresh'},
    };

    return {
      restrict: 'E',
      scope: {
        click: '&',
        action: '@'
      },
      link: function(scope, element){
        var html =
          '<i'
          + ' class="fas ' + iconTypes[scope.action].iconName + '"'
          + ' tp-text="' + iconTypes[scope.action].helpText + '" '
          + ' tooltip tp-class="tooltip" '
          + ' tp-x="-50" tp-y="-150" '
          + ' tp-anchor-x="0" tp-anchor-y="0"'
          + ' style="margin-left: 0.5em; font-size: 14px"'
          + ' ng-click="click()"'
          + '></i>';
        var el = $compile(html)(scope);
        element.append(el);
      }
    }
  });

});
