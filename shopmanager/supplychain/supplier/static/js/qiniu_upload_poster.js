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
            'UploadComplete': function () {
                //$('#success').show();
            },
            'FileUploaded': function (up, file, info) {
                var domain = up.getOption('domain');
                var res = jQuery.parseJSON(info);
                var sourceLink = domain + res.key; //获取上传成功后的文件的Url
                console.log('sourceLink:', sourceLink);
                saveLinkDb(sourceLink)
            },
            'Error': function (up, err, errTip) {
            }
            ,
            'Key': function (up, file) {
                var key = FileNameHandler(file.name, 'post');
                return key
            }
        }
    });
});

function saveLinkDb(sourceLink) {
    var requestUrl = '/mm/post_poster/';
    var date = getUrlParam('date');
    var categray = getUrlParam('categray');
    console.log(categray, date);
    var data = {"date": date, "categray": categray, "pic_link": sourceLink};
    $("#preview").attr("src", sourceLink);
    function requestCallbck(res) {
        console.log("服务器返回结果：", res);
        // 上传成功后　将返回的　海报链接显示到原来的按钮上面
        if (res.code == 0) {
            alert('确少参数')
        }
        else if (res.code == 1) {
            layer.msg('修改童装海报成功');
            window.close();
        }
        else if (res.code == 2) {
            layer.msg('修改女装海报成功');
        }
        else if (res.code == 3) {
            alert('多个海报对象')
        }
        else if (res.code == 4) {
            alert('ValueError')
        }
        else if (res.code == 5) {
            alert('类别缺失')
        }
        else {
            alert('系统错误')
        }
    };
    $.ajax({
        url: requestUrl,
        data: data,
        type: "post",
        dataType: 'json',
        success: requestCallbck
    });
}