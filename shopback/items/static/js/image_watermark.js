$(function(){
    var FILE_BUTTON_HTML = '<a id="upload-image" href="javascript:void(0)">' +
            '<img height="10px" width="10px" alt="上传图片" src="/static/admin/img/icon_addlink.gif"></img>'+
            '</a>';
    $('#imagewatermark_form input[name="url"]').after(FILE_BUTTON_HTML);

    var uploader = Qiniu.uploader({
        runtimes: 'html5, flash, html4',
        browse_button: 'upload-image',
        container: 'container',
        uptoken_url: '/mm/qiniu/?format=json',
        flash_swf_url: 'js/plupload/Moxie.swf',
        domain: 'http://img.xiaolumeimei.com',
        max_retires: 3,
        auto_start: true,
        unique_names: true,
        init: {
            FileUploaded: function(up, file, info){
                var parsed_info = $.parseJSON(info);
                var url = up.getOption('domain') + '/' + encodeURI(parsed_info.key);
                $('#imagewatermark_form input[name="url"]').val(url);
            }
        }
    });
});
