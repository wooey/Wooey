var $ = django.jQuery;
$(document).ready(function(){
    var default_version_selector = '.field-default_version > input';
    var $default_script_versions = $(default_version_selector);
    $default_script_versions.click(function(event){
        var $this = $(this);
        var checked = $this.is(':checked');
        if( checked === true){
            // remove all other checks
            $(default_version_selector).each(function(index, value){
                if(value.id != $this.attr('id')){
                    $(value).prop('checked', false)
                }
            });
        }
        else{
            // if we are the sole check, do not remove it
            if(!($(default_version_selector).is(':checked'))){
                $this.prop('checked', true);
            }
        }
    });
});