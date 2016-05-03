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
            scope: { 'table': '='},
            templateUrl: './js/modules/common/entry-table.html',
            link: function (scope) {

                scope.addBlankRow = function (table) {
                    var n_var = table.titles.length;
                    var row = [];
                    for (var j = 0; j < n_var; j += 1) {
                        row.push("");
                    }
                    table.rows.push(row);
                    table.iEditRow = table.rows.length - 1;
                };

                scope.deleteRow = function (table, iRow) {
                    var iLastRow = table.rows.length - 1;
                    table.rows.splice(iRow, 1);
                    if (iLastRow == iRow) {
                        scope.addBlankRow(table);
                    }
                    table.iEditRow = table.rows.length - 1;
                    table.validateFn(table);
                };

                scope.editRow = function (table, iRow) {
                    var iLastRow = table.rows.length - 1;
                    if (table.iEditRow == iLastRow) {
                        table.rows.splice(iLastRow, 1);
                    }
                    table.iEditRow = iRow;
                };

                scope.acceptEdit = function (table) {
                    scope.addBlankRow(table);
                    table.validateFn(table);
                };

                scope.$watch(
                    'table',
                    function () {
                        var table = scope.table;
                        if (_.isUndefined(table.iEditRow)) {
                            scope.addBlankRow(table);
                        }
                    },
                    true
                );

            }
        }

    });

    return module;

});
