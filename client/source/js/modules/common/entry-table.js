define(['angular', 'underscore', 'jquery'], function (angular, _, $) {

    'use strict';

    var module = angular.module('app.common.entry-table', []);

    module.directive('entryTable', function () {

        /*
        Example of table dictionary that <entry-table> can handle:

            {
              "titles": [
                "Year",
                "Saturation % (low)",
                "Saturation % (High)",
                "Unitcost (low)",
                "Unitcost (high)"
              ],
              "rows": [
                [
                  2016,
                  90,
                  90,
                  155.52121304634755,
                  155.52121304634755
                ],
                [
                  2017,
                  40,
                  90,
                  2,
                  300
                ]
              ],
              "types": [
                "number",
                "number",
                "number",
                "number",
                "number"
              ],
              "widths": []
            }
         */

        return {
            scope: { 'table': '=' },
            templateUrl: './js/modules/common/entry-table.html',
            link: function (scope) {

                scope.addBlankRow = function () {
                    var n_var = scope.table.titles.length;
                    var row = [];
                    for (var j = 0; j < n_var; j += 1) {
                        row.push("");
                    }
                    scope.table.rows.push(row);
                    scope.table.iEditRow = scope.table.rows.length - 1;
                };

                scope.deleteRow = function (iRow) {
                    var iLastRow = scope.table.rows.length - 1;
                    scope.table.rows.splice(iRow, 1);
                    if (iLastRow == iRow) {
                        scope.addBlankRow(scope.table);
                    }
                    scope.table.iEditRow = scope.table.rows.length - 1;
                    scope.table.validateFn(scope.table);
                };

                scope.editRow = function (iRow) {
                    var iLastRow = scope.table.rows.length - 1;
                    if (scope.table.iEditRow == iLastRow) {
                        scope.table.rows.splice(iLastRow, 1);
                    }
                    scope.table.iEditRow = iRow;
                };

                scope.acceptEdit = function () {
                    scope.addBlankRow(scope.table);
                    scope.table.validateFn(scope.table);
                };

                scope.displayRow = function (row) {
                    var result = [];
                    for (var i=0; i<row.length; i+=1) {
                        var val = row[i];
                        if (scope.table.types[i] == "displayFn") {
                            var fn = scope.table.displayRowFns[i];
                            if (fn) {
                                val = fn(row);
                            }
                        }
                        result.push(val);
                    }
                    return result;
                };

                scope.$watch(
                    'table',
                    function () {
                        if (_.isUndefined(scope.table)) {
                            return;
                        }
                        if (_.isUndefined(scope.table.iEditRow)) {
                            scope.addBlankRow(scope.table);
                        }
                    },
                    true
                );

            }
        }

    });

    return module;

});
