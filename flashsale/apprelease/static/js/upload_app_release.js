/**
 * Created by jishu_linjie on 1/13/16.
 */

$(function () {
    var uploader = Qiniu.uploader({
        runtimes: 'html5,flash,html4',
        browse_button: 'pickfiles',
        container: 'uploadfile',
        max_file_size: '100mb',
        flash_swf_url: 'js/plupload/Moxie.swf',
        chunk_size: '4mb',
        uptoken_url: $('#uptoken_url').val(),
        domain: $('#domain').val(),
        auto_start: true,
        init: {
            'FilesAdded': function (up, files) {
            },
            'BeforeUpload': function (up, file) {
            },
            'UploadProgress': function (up, file) {
            },
            'UploadComplete': function (up, file, info) {
            },
            'FileUploaded': function (up, file, info) {
                var domain = up.getOption('domain');
                var res = jQuery.parseJSON(info);
                var pic_link = domain + res.key; //获取上传成功后的文件的Url
                $("#download_link").val(pic_link);// 填写url到页面
            },
            'Error': function (up, err, errTip) {
            }
            ,
            'Key': function (up, file) {
                var timestamp = new Date().getTime();
                var version = $("#version").val();
                var key = "xlmm_" + timestamp + file.name;
                return key
            }
        }
    });
});


$(function () {
    var uploader = Qiniu.uploader({
        runtimes: 'html5,flash,html4',
        browse_button: 'pick_qrcode_files',
        container: 'upload_qrcode_file',
        max_file_size: '100mb',
        flash_swf_url: 'js/plupload/Moxie.swf',
        chunk_size: '4mb',
        uptoken_url: $('#uptoken_url').val(),
        domain: $('#domain').val(),
        auto_start: true,
        init: {
            'FilesAdded': function (up, files) {
            },
            'BeforeUpload': function (up, file) {
            },
            'UploadProgress': function (up, file) {
            },
            'UploadComplete': function (up, file, info) {
            },
            'FileUploaded': function (up, file, info) {
                var domain = up.getOption('domain');
                var res = jQuery.parseJSON(info);
                var pic_link = domain + res.key; //获取上传成功后的文件的Url
                $("#qrcode_link").val(pic_link);// 填写url到页面
            },
            'Error': function (up, err, errTip) {
            }
            ,
            'Key': function (up, file) {
                var timestamp = new Date().getTime();
                var version = $("#version").val();
                var key = "xlmm_" + timestamp + file.name;
                return key
            }
        }
    });
});

