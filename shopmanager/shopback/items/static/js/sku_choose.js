$(function () {
    $(".color-choose").click(dynamic_generate_sku);
    $(".sku-choose").click(dynamic_generate_sku);
    $(".sku-choose").click(dynamic_generate_chi);
    $(".chima-choose").click(dynamic_generate_chi);
    $("#chima-add").click(function () {
        var chimatext = $(".chima-add").val().trim();
        if (chimatext.length > 0) {
            $(".chima-content").append(template("chima-one", {"chima": chimatext}));
            $(".sku-choose").click(dynamic_generate_chi);
            $(".sku-choose").click(dynamic_generate_sku);
        }else{
             swal("填写空白", "(^_^)", "warning");
        }
    });
    $("#color-add").click(function () {
        var colortext = $(".color-add").val().trim();
        console.log(colortext.length)
        if (colortext.length > 0) {
            $(".color-content").append(template("color-one", {"color": colortext}));
            $(".color-choose").click(dynamic_generate_sku);
        }else{
            swal("填写空白", "(^_^)", "warning");
        }
    });
})
function dynamic_generate_sku() {
    var all_color = $(".color-choose");
    var all_sku = $(".sku-choose");
    var color = [];
    var count1 = 0;
    var sku = [];
    $.each(all_color, function (index, one_color) {
        if (one_color.checked) {
            color[count1++] = one_color.defaultValue;
        }
    });
    var count2 = 0;
    $.each(all_sku, function (i, one_sku) {
        if (one_sku.checked) {
            sku[count2++] = one_sku.defaultValue;
        }
    });
    if (count1 == 0 || count2 == 0) {
        $('#table-id tbody').html("");
    } else {
        var result = {
            title: '渲染',
            color: color,
            color_size: count1,
            sku: sku,
            sku_size: count2
        };
        var html = template('tr-template', result);
        $('#table-id tbody').html(html);
    }
    $(".c_remainnum").change(function(){
        $('input[id$=remainnum]').val($(this).val());
    });
    $(".c_cost").change(function(){
        $('input[id$=cost]').val($(this).val());
    });
    $(".c_pricestd").change(function(){
        $('input[id$=pricestd]').val($(this).val());
    });
    $(".c_agentprice").change(function(){
        $('input[id$=agentprice]').val($(this).val());
    });

}

function dynamic_generate_chi() {

    var all_sku = $(".sku-choose");
    var all_check = $(".chima-choose");
    var sku = [];
    var chi_ma = [];
    var count1 = 0;
    var count2 = 0;
    $.each(all_sku, function (i, one_sku) {
        if (one_sku.checked) {
            sku[count1++] = one_sku.defaultValue;
        }
    });

    $.each(all_check, function (j, one_chi) {
        if (one_chi.checked) {
            chi_ma[count2++] = one_chi.defaultValue;
        }
    });

    if (count1 == 0 || count2 == 0) {
        $('#chima-table thead').html("");
        $('#chima-table tbody').html("");
    } else {
        var result = {
            title: '渲染',
            sku: sku,
            sku_size: count1,
            chi_ma: chi_ma,
            chi_size: count2
        };
        var html = template('chi-template', result);
        var thead = template('thead-template', result);
        $('#chima-table thead').html(thead);
        $('#chima-table tbody').html(html);
    }
}