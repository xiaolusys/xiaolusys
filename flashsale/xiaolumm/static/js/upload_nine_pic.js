/**
 * Created by jishu_linjie on 1/13/16.
 */

$(function () {
    var nine_pics = [];
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
                saveLinkDb(nine_pics);
            },
            'FileUploaded': function (up, file, info) {
                var domain = up.getOption('domain');
                var res = jQuery.parseJSON(info);
                var pic_link = domain + res.key; //获取上传成功后的文件的Url
                console.log('sourceLink:', pic_link);
                nine_pics.push(pic_link);
            },
            'Error': function (up, err, errTip) {
            }
            ,
            'Key': function (up, file) {
                var timestamp = new Date().getTime();
                var key = "poster_" + timestamp;
                return key
            }
        }
    });
});

function saveLinkDb(nine_pics) {
    console.log("完成上传图片数组：", nine_pics);
    var pic_num = $("#category_choices").val();
    if (nine_pics.length != pic_num) {
        layer.msg("上传有误,没有" + pic_num + "张请重新上传！");
        return
    }
    var pic_arry = "";
    $.each(nine_pics, function (k, v) {
        if (k + 1 == nine_pics.length) {
            pic_arry += v;
        }
        else {
            pic_arry += v + ","
        }
    });
    var requestUrl = '/m/adver_nine_pic/';
    // 获取标题

    var title = $("#title_adv").val();// 标题
    var start_time = $("#current_date").html() + $("#start_ime").val();//开始展示时间
    var turns_num = $(".turns_num").length + 1;//第几轮 新建在现有轮数加１
    var cate_gory = $("#category_choices").val();
    var description = $("#description").val();
    console.log(title, start_time, turns_num, description);

    var data = {
        "title": title,
        "start_time": start_time,
        "turns_num": turns_num,
        "pic_arry": pic_arry,
        "cate_gory": cate_gory,
        "description": description
    };

    function requestCallbck(res) {
        console.log("服务器返回结果：", res);
        if (res.code == 1) {
            location.reload();//刷新
        }
        else {
            layer.msg("查看是否有时间重复，未知错误联系管理员！")
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
