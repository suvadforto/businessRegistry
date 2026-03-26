// obrt_toggle.js
django.jQuery(document).ready(function() {
    // Replace 'your_field_id' with the actual ID of the field wrapper
    var fieldWrapper = django.jQuery('#id_your_field_id').closest('.form-row'); 

    function toggleField() {
        // Replace 'other_field_id' with the select field controlling this logic
        var selected = django.jQuery('#id_other_field_id').val();
        if (selected === 'obrtnička') {
            fieldWrapper.show();
        } else {
            fieldWrapper.hide();
        }
    }

    // Run on page load
    toggleField();

    // Run whenever the controlling field changes
    django.jQuery('#id_other_field_id').change(function() {
        toggleField();
    });
});
alert(gettext("Available Additional Activities"));