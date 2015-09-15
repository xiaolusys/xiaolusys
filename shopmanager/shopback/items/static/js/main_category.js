var items;
var suppliers;
$(function () {
    get_category();
    get_supplier();
    $("#shelf_time").datepicker({
        dateFormat: "yy-mm-dd"
    });
    $('#new-product').bind("click", submit_data);
})
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

function showSupplier() {
    //显示供应商
    var supplier = new Supplier();
    $("#supplier").select2();
    supplier.fillOption('supplier', '0');
}
function get_category() {
    //获取分类信息
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
        success: requestCallBack,
        error: function (data) {
            if (data.status == 403) {
                swal({
                    title: "Tips",
                    text: "请先登录一下(^_^)",
                    type: "warning",
                    showCancelButton: false,
                    confirmButtonText: "确定"
                }, function () {
                    window.location = "/admin";
                });
            } else {
                swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
            }
        }
    });
}
function get_supplier() {
    //获取所有的供应商
    var requestUrl = "/items/get_supplier/";
    var urlParams = window.location.href.split('?');
    var supplier_id;
    if (urlParams.length < 2) {
        supplier_id = 0;
    } else {
        supplier_id = urlParams[1].split('=').length >= 1 ? urlParams[1].split('=')[1] : 0;
    }

    //请求成功回调函数
    var requestCallBack = function (all_supplier) {
        suppliers = all_supplier;
        showSupplier();
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {"supplier_id": supplier_id},
        dataType: 'json',
        success: requestCallBack,
        error: function (data) {
                    if (data.status == 403) {
                        swal({
                            title: "Tips",
                            text: "请先登录一下(^_^)",
                            type: "warning",
                            showCancelButton: false,
                            confirmButtonText: "确定"
                        }, function () {
                            window.location = "/admin";
                        });
                    } else {
                        swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
                    }
                }
    });
}
function get_all_check_color() {
    /*
     * 得到所有选中的颜色
     * auther:yann
     * date:2015/28/8
     */
    var color = [];
    var count = 0;
    $.each($(".color-choose"), function (index, one_color) {
        if (one_color.checked) {
            color[count++] = one_color.defaultValue;
        }
    });
    return color
}
function get_all_sku() {
    /*
     * 得到所有选中的sku
     * auther:yann
     * date:2015/28/8
     */
    var skus = [];
    var count = 0;
    $.each($(".sku-choose"), function (index, one_sku) {
        if (one_sku.checked) {
            skus[count++] = one_sku.defaultValue;
        }
    });
    return skus
}
function get_all_chima() {
    /*
     * 得到所有选中的尺码
     * auther:yann
     * date:2015/28/8
     */
    var chi_ma = [];
    var count = 0;
    $.each($(".chima-choose"), function (index, one_chima) {
        if (one_chima.checked) {
            chi_ma[count++] = one_chima.defaultValue;
        }
    });
    return chi_ma
}
function submit_data() {
    //请求URL
    var requestUrl = "/items/add_item/";
    var first_category = $('#first_category').val();
    var second_category = $('#second_category').val();
    var third_category = $('#third_category').val();
    var category;
    if (third_category.length > 0) {
        category = third_category;
    } else if (second_category.length > 0) {
        category = second_category;
    } else if (first_category.length > 0) {
        category = first_category;
    } else {
        swal("warning", "please select category(^_^)", "error");
        return
    }
    var supplier = $('#supplier').val();
    var product_name = $('#product_name').val().trim();
    var header_img_content = $('#header_img_content').val().trim();
    var material = $('#material_id').val().trim();
    var shelf_time = $('#shelf_time').val().trim();
    var note = $('#note_id').val().trim();
    var ware_by = $('#ware_by').val().trim();
    var wash_instroduce = $('#wash_instroduce').val().trim();
    var all_color = get_all_check_color();
    var all_sku = get_all_sku();
    var all_chi_ma = get_all_chima();

    var all_color_str = "";
    var all_sku_str = "";
    var all_chima_str = "";
    for (var i = 0; i < all_color.length; i++) {
        if (i == all_color.length - 1) {
            all_color_str += all_color[i];
        } else {
            all_color_str += all_color[i] + ",";

        }

    }
    for (var i = 0; i < all_sku.length; i++) {
        if (i == all_sku.length - 1) {
            all_sku_str += all_sku[i];
        } else {
            all_sku_str += all_sku[i] + ",";
        }

    }
    for (var i = 0; i < all_chi_ma.length; i++) {
        if (i == all_chi_ma.length - 1) {
            all_chima_str += all_chi_ma[i];
        } else {
            all_chima_str += all_chi_ma[i] + ",";
        }

    }
    if (product_name == "" || supplier == ""
        || material == "" || all_color_str == ""
        || all_sku_str == "" || all_chima_str == ""
        || shelf_time == "" || header_img_content == ""
        || wash_instroduce == "") {
        swal("tips", "请填写完整的基本信息(^_^)", "error");
        return
    }
    var all_input = $("table input");
    for (var i = 0; i < all_input.length; i++) {
        if (all_input.eq(i).val().trim() == "") {
            swal("tips", "请填写完整的商品数据(^_^)", "error");
            return;
        }
    }
    var result_data = {
        product_name: product_name,
        category: category,
        supplier: supplier,
        material: material,
        note: note,
        all_colors: all_color_str,
        all_sku: all_sku_str,
        all_chima: all_chima_str,
        header_img: header_img_content,
        wash_instroduce: wash_instroduce,
        shelf_time: shelf_time,
        ware_by: ware_by
    };
    for (var i = 0; i < all_color.length; i++) {
        var one_color = all_color[i].replace("+","\\+");
        for (var j = 0; j < all_sku.length; j++) {
            result_data[all_color[i] + "_" + all_sku[j] + "_remainnum"] = $("#" + one_color + "_" + all_sku[j] + "_remainnum").val();
            result_data[all_color[i] + "_" + all_sku[j] + "_cost"] = $("#" + one_color + "_" + all_sku[j] + "_cost").val();
            result_data[all_color[i] + "_" + all_sku[j] + "_pricestd"] = $("#" + one_color + "_" + all_sku[j] + "_pricestd").val();
            result_data[all_color[i] + "_" + all_sku[j] + "_agentprice"] = $("#" + one_color + "_" + all_sku[j] + "_agentprice").val();
        }

    }

    for (var k = 0; k < all_sku.length; k++) {
        for (var h = 0; h < all_chi_ma.length; h++) {
            result_data[all_sku[k] + "_" + all_chi_ma[h] + "_size"] = $("#" + all_sku[k] + "_" + all_chi_ma[h] + "_size").val();
        }
    }
    //请求成功回调函数
    var requestCallBack = function (data) {
        console.log(data);
        if (data.result == "OK") {
            swal({
                title: "恭喜",
                text: "添加成功(^_^)",
                type: "success",
                showCancelButton: false,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "确定",
                closeOnConfirm: false
            }, function () {
                window.location = "/admin/items/product/?q=" + data.outer_id;
            });
        } else {
            swal("内部错误(^_^)", data.result, "error");
            $('#new-product').bind("click", submit_data);
        }
    };

    swal({
            title: "",
            text: "确定要提交了吗？",
            type: "",
            showCancelButton: true,
            imageUrl: "http://image.xiaolu.so/logo.png",
            confirmButtonColor: '#DD6B55',
            confirmButtonText: '确定',
            cancelButtonText: '取消'
        },
        function () {
            $("#new-product").unbind();
            //发送请求
            $.ajax({
                type: 'post',
                url: requestUrl,
                data: result_data,
                dataType: 'json',
                success: requestCallBack,
                error: function (data) {
                    if (data.status == 403) {
                        swal({
                            title: "Tips",
                            text: "请先登录一下(^_^)",
                            type: "warning",
                            showCancelButton: false,
                            confirmButtonText: "确定"
                        }, function () {
                            window.location = "/admin";
                        });
                    } else {
                        swal("Tips", "有错误，请联系技术人员(^_^)", "warning")
                    }
                }
            });
        });


}