function showCategory(first_cate, second_cate, third_cate) {

    var loc = new Category();
    var title = ['一级', '2级', '3级'];
    $.each(title, function (k, v) {
        title[k] = '<option value="">' + v + '</option>';
    })

    $('#first_category').append(title[0]);
    $('#second_category').append(title[1]);
    $('#third_category').append(title[2]);

    $("#first_category,#second_category,#third_category").select2()
    $('#first_category').change(function () {
        $('#second_category').empty();
        $('#second_category').append(title[1]);
        loc.fillOption('second_category', '0,' + $('#first_category').val());
        $('#second_category').change()
    })

    $('#second_category').change(function () {
        $('#third_category').empty();
        $('#third_category').append(title[2]);
        loc.fillOption('third_category', '0,' + $('#first_category').val() + ',' + $('#second_category').val());
    })

    $('#third_category').change(function () {
        $('input[name=location_id]').val($(this).val());
    })

    if (first_cate) {
        loc.fillOption('first_category', '0', first_cate);

        if (second_cate) {
            loc.fillOption('second_category', '0,' + first_cate, second_cate);

            if (third_cate) {
                loc.fillOption('third_category', '0,' + first_cate + ',' + second_cate, third_cate);
            }
        }

    } else {
        loc.fillOption('first_category', '0');
    }

}
var items;
function get_category() {
    console.log("fff");
    var requestUrl = "/items/get_category/";

    //请求成功回调函数
    var requestCallBack = function (data) {

        items = data;
        showCategory();
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        success: requestCallBack
    });
}
$(function () {
    get_category();
    $("#f_datepicker").datepicker({
        dateFormat: "yy-mm-dd"
    });
    $('#btnval').click(function () {
        alert($('#first_category').val() + ' - ' + $('#second_category').val() + ' - ' + $('#third_category').val())
    })
    $('#btntext').click(function () {
        alert($('#first_category').select2('data').text + ' - ' + $('#second_category').select2('data').text + ' - ' + $('#third_category').select2('data').text)
    })
})
