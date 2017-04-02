/**
 * Created by yann on 15-7-10.
 */
function show_pic(id) {
    var gallery = $('.popup-gallery');
    var gallery_img = $('.popup-gallery a');
    gallery_img.remove();
    $.get('/sale/dinghuo/show_pic/' + id, function (result_data) {
        var obj = result_data.split(",");
        $.each(obj, function (index, value) {
            gallery.append('<a class="example-image-link" style="display:None" href="' + value + '" data-lightbox="example-1">ttt</a>');
        });
        var example = $(".example-image-link");
        if (example.length > 0) {
            example.trigger("click");
        }
    });


}

$(document).ready(function () {
    var model_num = 0;
    var quantity = 0;
    var amount = 0;
    var lib_amount = 0;
    for (var j = 0; j < $("tbody tr").length; j++) {
        model_num += parseInt($("tbody tr:eq(" + j + ")").children("td:eq(5)").html());
        quantity += parseInt($("tbody tr:eq(" + j + ")").children("td:eq(4)").html());
        lib_amount += parseInt($("tbody tr:eq(" + j + ")").children("td:eq(3)").html());
        amount += parseInt($("tbody tr:eq(" + j + ")").children("td:eq(2)").html());

    }
    var value = lib_amount - amount;
    var tip_str = '共: ' + model_num + ' 款 ' + quantity + ' 件 ' +
        amount + ' ￥ ' + "录入总价为：" + lib_amount + '　节省　' + value + '￥ (200秒消失)';
    layer.tips(tip_str, $('input')[1], {
        tips: [1, '#18A15F'],
        time: 200000
    });
});
