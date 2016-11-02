var SGCM_OF_CHILDREN = ['52-59', '59-73', '73-80', '75-85', '85-95', '95-105', '105-115',
                        '115-125', '125-135', '135-145', '145-155', '155-165'];

$(function () {
    $(".color-choose").click(dynamic_generate_sku);
    $(".sku-choose").click(dynamic_generate_sku);
    $(".sku-choose").click(dynamic_generate_chi);
    $(".chima-choose").click(dynamic_generate_chi);

    $("#chima-add").click(function () {
        var chimatext = $(".chima-add").val().trim();
        if (chimatext.length > 0) {
            $("#sku-group-5 .panel-body").append(template("chima-one", {"chima": chimatext}));
            if($('#sku-group-5').is(':hidden'))
                $('#sku-group-5').show();
            $(".sku-choose").click(dynamic_generate_chi);
            $(".sku-choose").click(dynamic_generate_sku);
            dynamic_generate_chi();
            dynamic_generate_sku();
        }else{
            swal("填写空白", "(^_^)", "warning");
        }
    });
    $("#color-add").click(function () {
        var colortext = $(".color-add").val().trim();
        if (colortext.length > 0) {
            $("#other-colors").append(template("color-one", {"color": colortext}));
            $(".color-choose").click(dynamic_generate_sku);
            dynamic_generate_sku();
        }else{
            swal("填写空白", "(^_^)", "warning");
        }
    });
    $('#duizhao-add').click(function(){
        var duizhaotext = $('.duizhao-add').val();
        if(duizhaotext && duizhaotext.length > 0){
            $('#chima-group-4').parent().append(template('duizhao-one', {duizhao: duizhaotext.trim()}));
            $('.chima-choose').click(dynamic_generate_chi);
            dynamic_generate_chi();
        }
    });
});
function dynamic_generate_sku() {
    var all_color = $(".color-choose");
    var all_sku = $(".sku-choose");
    var color = [];
    var count1 = 0;
    var sku = [];
    var sku_of_number = [];
    var sku_of_character = [];
    $.each(all_color, function (index, one_color) {
        if (one_color.checked) {
            color[count1++] = one_color.defaultValue;
        }
    });
    var count2 = 0;
    $.each(all_sku, function (i, one_sku) {
        if (one_sku.checked) {
            if(isNaN(one_sku.defaultValue))
                sku_of_character.push(one_sku.defaultValue);
            else
                sku_of_number.push(parseInt(one_sku.defaultValue));
            count2++;
        }
    });
    if (count1 == 0 || count2 == 0) {
        $('#table-id tbody').html("");
    } else {
        sku = _.sortBy(sku_of_number).concat(sku_of_character);
        var result = {
            title: '渲染',
            color: color,
            color_size: count1,
            sku: _.map(sku, function(el){
                return {id: String(el).replace(/[\/ 　:]/g, ''), label: el};
            }),
            sku_size: count2
        };
        var html = template('tr-template', result);
        $('#table-id tbody').html(html);
    }
    $(".c_outerid:first").change(function(){
        var value = $(this).val();
        var prefix = '';
        var count  = 1;
        if (value.trim() == '')return;
        prefix = value.replace(/(^[\s-]*)|([\s-]*$)/g, "");
        prefix += '-';
        $('input[id$=outerid]').each(function(n,e){
            $(e).val(prefix+count);
            count ++;
        });
    });
    $(".c_remainnum:first").change(function(){
        $('input[id$=remainnum]').val($(this).val());
    });
    $(".c_cost:first").change(function(){
        $('input[id$=cost]').val($(this).val());
    });
    $(".c_pricestd:first").change(function(){
        $('input[id$=pricestd]').val($(this).val());
    });
    $(".c_agentprice:first").change(function(){
        $('input[id$=agentprice]').val($(this).val());
    });
    if(saleproduct.supplier_sku){
        var prefix = '';
        var count = 1;
        prefix = saleproduct.supplier_sku.replace(/(^[\s-]*)|([\s-]*$)/g, "")+'-';
        $('input[id$=outerid]').each(function(i, el){
            $(el).val(prefix+count);
            count++;
        });
    }
    if(!isNaN(saleproduct.remain_num)){
        $('input[id$=remainnum]').val(saleproduct.remain_num);
    }
    if(!isNaN(saleproduct.sale_price)){
        $('input[id$=cost]').val(saleproduct.sale_price);
    }
    if(!isNaN(saleproduct.on_sale_price)){
        $('input[id$=agentprice]').val(saleproduct.on_sale_price);
    }
    if(!isNaN(saleproduct.std_sale_price)){
        $('input[id$=pricestd]').val(saleproduct.std_sale_price);
    }
}

function dynamic_generate_chi() {
    var all_sku = $(".sku-choose");
    var all_check = $(".chima-choose");
    var sku = [];
    var chi_ma = [];
    var count1 = 0;
    var count2 = 0;
    var sku_of_number = [];
    var sku_of_character = [];
    $.each(all_sku, function (i, one_sku) {
        if (one_sku.checked) {
            if(isNaN(one_sku.defaultValue))
                sku_of_character.push(one_sku.defaultValue);
            else
                sku_of_number.push(parseInt(one_sku.defaultValue));
            count1++;
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
        sku = _.sortBy(sku_of_number).concat(sku_of_character);
        var result = {
            title: '渲染',
            sku: _.map(sku, function(el){
                return {id: String(el).replace(/[\/ 　:]/g, ''), label: el};
            }),
            sku_size: count1,
            chi_ma: chi_ma,
            chi_size: count2
        };
        var html = template('chi-template', result);
        var thead = template('thead-template', result);
        $('#chima-table thead').html(thead);
        $('#chima-table tbody').html(html);
        $('#chima-table td:nth-child(3) input').unbind().bind('blur', function(){
            var value = $(this).val().trim();
            var step = $(this).closest('tr').find('select option:selected').val() - 0;
            var base = $(this).val() - 0;
            //建议身高单独判断
            if($(this).prop('id').indexOf('建议身高') != -1){
                var indexOfCM = SGCM_OF_CHILDREN.indexOf(value);
                if(indexOfCM != -1){
                    $(this).closest('td').nextAll().find('input').each(function(i, el){
                        $(el).val(SGCM_OF_CHILDREN[indexOfCM + i + 1]);
                    });
                }
            }
            else if(base){
                $(this).closest('td').nextAll().find('input').each(function(i, el){
                    $(el).val(base + step * (i + 1));
                });
            }
        });
    }
}
