
var items;
var suppliers;
var supplier_id;
var saleproduct_id;
var saleproduct;
var wash_tip = "洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。";
$(function () {

    $("#shelf_time").datepicker({
        dateFormat: "yy-mm-dd"
    });

    $('.checkbox-group-choose').change(function(){
        var checkbox_group_id = '#' + $(this).val();
        if($(this).prop('checked'))
            $(checkbox_group_id).show();
        else{
            $(checkbox_group_id+' :checkbox').prop('checked', false);
            $(checkbox_group_id).hide();
        }
    });
    $('#no-chima').change(function(){
        if($(this).prop('checked')){
            $('#chima-table').hide();
        }
        else{
            $('#chima-table').show();
        }
    });

    var urlParams = parseUrlParams(window.location.href);
    supplier_id = urlParams["supplier_id"];
    saleproduct_id = urlParams["saleproduct"];
    if(!supplier_id || !saleproduct_id){
        alert("请从选品列表进来");
        return;
    }
    saleproduct = get_sale_product(saleproduct_id);
    get_category(saleproduct.product_category);
    get_supplier();
    $('#new-product').bind("click", submit_data);
});
function get_sale_product(saleproduct_id){
    //获取选品信息
    var obj;
    $.ajax({
        async: false,
        type: 'get',
        dataType: 'json',
        url: '/supplychain/supplier/product/' + saleproduct_id,
        success: function(result){
            if(result.sale_time)
                $('#shelf_time').val(result.sale_time);
            $('#header_img_content').val(result.pic_url);
            obj = result;
        }
    });
    return obj;
}
function parseUrlParams(myUrl) {
    var vars = [], hash;
    var hashes = window.location.href.slice(myUrl.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}
function showCategory(first_cate, second_cate, third_cate) {

    var loc = new Category();

    var title = ['一级', '2级', '3级'];
    $.each(title, function (k, v) {
        title[k] = '<option value="">' + v + '</option>';
    });


    $('#first_category').append(title[0]);
    $('#second_category').append(title[1]);
    $('#third_category').append(title[2]);


    $("#first_category,#second_category,#third_category").select2();
    $('#first_category').change(function () {

        $('#second_category').empty();
        $('#second_category').append(title[1]);
        loc.fillOption('second_category', '0,' + $('#first_category').val());
        $('#second_category').change();
    });

    $('#second_category').change(function () {
        if(this.value==5){
            $("#wash_instroduce").val(wash_tip);
        }else{
            $("#wash_instroduce").val("");
        }
        $('#third_category').empty();
        $('#third_category').append(title[2]);
        loc.fillOption('third_category', '0,' + $('#first_category').val() + ',' + $('#second_category').val());
    });

    $('#third_category').change(function () {
        $('input[name=location_id]').val($(this).val());
    });

    var level_2_name = '', level_3_name= '';
    loc.fillOption('first_category', '0', first_cate);
    if(first_cate){
        loc.fillOption('second_category', '0,' + first_cate, second_cate);
        level_2_name = loc.getName('0,' + first_cate, second_cate);
    }
    if(second_cate){
        loc.fillOption('third_category', '0,' + first_cate + ',' + second_cate, third_cate);
        level_3_name = loc.getName('0,' + first_cate + ',' + second_cate, third_cate);
    }
    if(level_3_name == '内衣'){
        $('#sku-group-2-choose').trigger('click');
        $('#chima-group-3-choose').trigger('click');
        $('input[value="上胸围"], input[value="下胸围"]').trigger('click');
    }
    else{
        if(level_2_name == '女装')
            $('#sku-group-1-choose').trigger('click');
        else if(level_2_name == '童装'){
            $('#sku-group-3-choose').trigger('click');
            $('#jysg-choose').trigger('click');
        }
    }
    if(['上装', '外套', '连衣裙'].indexOf(level_3_name) != -1){
        $('#chima-group-1-choose').trigger('click');
        if(['上装', '外套'].indexOf(level_3_name) != -1){
            $('input[value="衣长"], input[value="肩宽"], input[value="袖长"], #chima-group-1 input[value="胸围"]').trigger('click');
        }
        else{
            $('#chima-group-1 input[value="裙长"], input[value="肩宽"], input[value="袖长"], #chima-group-1 input[value="胸围"]').trigger('click');
        }
    }
    else if(level_3_name == '下装'){
        $('#chima-group-2-choose').trigger('click');
        $('input[value="裤长"], input[value="腰围"]', '#chima-group-2').trigger('click');
    }
    else if(level_3_name == '套装'){
        $('#chima-group-1-choose').trigger('click');
        $('#chima-group-2-choose').trigger('click');
        $('input[value="衣长"], input[value="肩宽"], input[value="袖长"]').trigger('click');
        $('input[value="裤长"], input[value="腰围"]', '#chima-group-2').trigger('click');
    }
}

function showSupplier() {
    //显示供应商
    var supplier = new Supplier();
    $("#supplier").select2();
    supplier.fillOption('supplier', '0');
}
function get_category(productCategory) {
    //获取分类信息
    var requestUrl = "/items/get_category/";

    //请求成功回调函数
    var requestCallBack = function (data) {
        items = data;
        showCategory(productCategory.level_1_id,
                     productCategory.level_2_id,
                     productCategory.level_3_id);
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
                swal("Tips", "有错误，请联系技术人员(^_^)", "warning");
            }
        }
    });
}
function get_supplier() {
    //获取所有的供应商
    var requestUrl = "/items/get_supplier/";

    //请求成功回调函数
    var requestCallBack = function (result) {
        var ware_by = result.ware_by;
        suppliers = result.all_supplier;
        showSupplier();
        if(ware_by)
            $('#ware_by').val(ware_by);
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
                        swal("Tips", "有错误，请联系技术人员(^_^)", "warning");
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
    return color;
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
    return skus;
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
    return chi_ma;
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
        return;
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
    var need_chima = true;
    if ($("#no-chima").attr("checked")) {
        need_chima = false;
    } else {
        need_chima = true;
    }

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
        || all_sku_str == "" || (all_chima_str == "" && need_chima)
        || shelf_time == "" || header_img_content == ""
        || wash_instroduce == "") {
        swal("tips", "请填写完整的基本信息(^_^)", "error");
        return
    }
    var all_input = $("table:visible input");
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
        ware_by: ware_by,
        saleproduct: saleproduct_id
    };
    for (var i = 0; i < all_color.length; i++) {
        var one_color = all_color[i].replace(/\+/g,"\\+").replace(/\[/g,"\\[").replace(/\]/g,"\\]").replace(/\*/g,"\\*");
        //console.log(one_color)
        for (var j = 0; j < all_sku.length; j++) {
            var one_sku = all_sku[j].replace(/[\/ 　:]/g, '');
            result_data[all_color[i] + "_" + all_sku[j] + "_outerid"] = $("#" + one_color + "_" + one_sku + "_outerid").val().trim();
            result_data[all_color[i] + "_" + all_sku[j] + "_remainnum"] = $("#" + one_color + "_" + one_sku + "_remainnum").val().trim();
            result_data[all_color[i] + "_" + all_sku[j] + "_cost"] = $("#" + one_color + "_" + one_sku + "_cost").val().trim();
            result_data[all_color[i] + "_" + all_sku[j] + "_pricestd"] = $("#" + one_color + "_" + one_sku + "_pricestd").val().trim();
            result_data[all_color[i] + "_" + all_sku[j] + "_agentprice"] = $("#" + one_color + "_" + one_sku + "_agentprice").val().trim();
        }
    }

    for (var k = 0; k < all_sku.length; k++) {
        var one_sku = all_sku[k].replace(/[\/ 　:]/g, '');
        for (var h = 0; h < all_chi_ma.length; h++) {
            result_data[all_sku[k] + "_" + all_chi_ma[h] + "_size"] = $("#" + one_sku + "_" + all_chi_ma[h] + "_size").val().trim();
        }
    }
    //请求成功回调函数
    var requestCallBack = function (data) {

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
            alert(data.result);
        }
    };

    swal({
            title: "",
            text: "确定要提交了吗？",
            type: "",
            showCancelButton: true,
            imageUrl: "http://img.xiaolumeimei.com/logo.png",
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
                        $('#new-product').bind("click", submit_data);
                        swal("Tips", "请先登录一下(^_^)", "warning");
                    } else {
                        $('#new-product').bind("click", submit_data);
                        swal("Tips", "有错误，请联系技术人员(^_^)", "warning");
                    }
                }
            });
        });
}
