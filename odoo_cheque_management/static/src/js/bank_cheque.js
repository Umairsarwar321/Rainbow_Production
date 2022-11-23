odoo.define('odoo_cheque_management.bank_cheque', function (require) {
    'use strict';
    $(document).ready(function () {
        var cheque_measure_unit = $(document).find('#cheque_measure_unit').first().text();
        var cheque_height = $(document).find('#cheque_height').first().text();
        var cheque_width = $(document).find('#cheque_width').first().text();

        jQuery(function ($) {
            var jcrop_api;
            $('#target').Jcrop({
                onChange: showCoords,
                onSelect: showCoords,
                onRelease: clearCoords
            }, function () {
                jcrop_api = this;
            });

            $('#coords').on('change', 'input', function (e) {
                var x1 = $('#x1').val(),
                    x2 = $('#x2').val(),
                    y1 = $('#y1').val(),
                    y2 = $('#y2').val();
                jcrop_api.setSelect([x1, y1, x2, y2]);
            });

        });

        // Simple event handler, called from onChange and onSelect
        // event handlers, as per the Jcrop invocation above
        function showCoords(c) {
            $('#x1').val(c.x);
            $('#y1').val(c.y);
            $('#x2').val(c.x2);
            $('#y2').val(c.y2);
            $('#w').val(c.w);
            $('#h').val(c.h);
        };
        function clearCoords() {
            $('#coords input').not("input[type='hidden']").val('');
        };
    });

});
