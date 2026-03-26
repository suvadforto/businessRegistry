(function($) {
    $(document).ready(function() {

        function toggleObrt() {

            var industry = $("#id_industry").val();
            var row = $(".form-row.field-obrt_type");

            if (industry === "obrt") {
                row.show();
            } else {
                row.hide();
                $("#id_obrt_type").val("");
            }
        }

        toggleObrt();

        $("#id_industry").change(function() {
            toggleObrt();
        });

    });
})(django.jQuery);