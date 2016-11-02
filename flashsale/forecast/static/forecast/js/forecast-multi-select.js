
function searchItemByIds(forecast_id, product_id, sku_id){
 var forecast = {};
 var product = {};
 var sku = {};
 for (var i=0; i<selectableItems.length; i++){
    forecast = selectableItems[i];
    for (var j=0; j<forecast.detail_products.length;j++){
        product = forecast.detail_products[j];
        for (var k=0; k< product.detail_skus.length; k++){
            sku = product.detail_skus[k];
            if (forecast_id==forecast.id
                && product_id==product.product_id
                && sku_id==sku.sku_id){
                return [forecast, product, sku];
            }
        }
    }
 }
}

/* function getValidTransDetail(){
var selectedInputs = $('input[name$=-selection-input].selected');
var selectedDatas = [];
for(var i=0; i<selectedInputs.length;i++){
    var $selectedInput = $(selectedInputs[i]);
    var dataId = $selectedInput.attr('data-id');
    var selected_num   = parseInt($selectedInput).val()||'0');
    var selectable_num = parseInt($('input[id='+ dataId +'-selectable-input]').val()||'0');
    var dataIds = dataId.split('-');
    var dataObj = {};
}
} */

/* function insertItems(skuId, productId, forecastId, num){
    var eForecast, eProduct, eSku =  searchItemByIds(forecastId, productId, skuId);totalNum
    for (var i=0; i<selectedItems.length; i++){
        forecast = selectedItems[i];
        for (var j=0; j<forecast.detailProducts.length;j++){
            product = forecast.detailProducts[j];
            for (var k=0; k< product.detailSkus.length; k++){
                sku = product.detailSkus[k];
                if (forecast_id==forecast.id
                    && product_id==product.product_id
                    && sku_id==sku.sku_id){
                    return [forecast, product, sku];
                }
            }
        }
    }
    selectedItems[selectedItems.length] = $.extend({}, eForecast);

} */


// 更新已选区选择商品列表
$('.ms-selectable a.select-all').click(function(){
 var data_id = $(this).attr('data-id');
 var select_all = $(this).attr('data-select-all')=='yes'?true:false;

 if (select_all){
     $('li[id$=' + data_id + '-selection-li]').removeClass('hidden').addClass('selected');

     var $optArrow = $('li[id=' + data_id + '-selection-li]').find('a.switch i:last');
     $optArrow.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');

     // 批量选中后隐藏
     var $selectableLi = $('li[id$=' + data_id + '-selectable-li]');
     $selectableLi.removeClass('selected').addClass('hidden');
 }else{
     var opt_data_id = data_id.substring(data_id.indexOf('-') + 1);
     $('li[id=' + opt_data_id + '-selection-li]').removeClass('hidden').addClass('selected');
     $('li[id=' + data_id + '-selection-li]').removeClass('hidden').addClass('selected');

     var $optArrow = $('li[id=' + opt_data_id + '-selection-li]').find('a.switch i:last');
     $optArrow.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
    　
     // 单SKU选中后隐藏
     $('li[id=' + data_id + '-selectable-li]').addClass('hidden').removeClass('selected');
     var $selectableLi = $('li[id$=-' + opt_data_id + '-selectable-li].selected');
     if ($selectableLi.length == 0){
        $('li[id=' + opt_data_id + '-selectable-li]').addClass('hidden').removeClass('selected');
     }
 }

 $('input[name$=' + data_id + '-selectable-input]').val(0);
 var $selectionInputs = $('input[name$=' + data_id + '-selection-input]');
 for (var i=0; i<$selectionInputs.length; i++){
    var $selectionInput = $($selectionInputs[i]);
    $selectionInput.val($selectionInput.attr('data-num'));
 }

});

// 取消已选区选择商品列表
$('.ms-selection a.cancel-all').click(function(){
 var data_id = $(this).attr('data-id');
 var cancel_all = $(this).attr('data-cancel-all')=='yes'?true:false;
 if (cancel_all){
     $('li[id$=' + data_id + '-selectable-li]').removeClass('hidden').addClass('selected');

     var $optArrow = $('li[id=' + data_id + '-selectable-li]').find('a.switch i:last');
     $optArrow.removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');

     $('li[id$=' + data_id + '-selection-li]').removeClass('selected').addClass('hidden');

 }else{
     var opt_data_id = data_id.substring(data_id.indexOf('-') + 1);
     $('li[id=' + opt_data_id + '-selectable-li]').removeClass('hidden').addClass('selected');
     $('li[id=' + data_id + '-selectable-li]').removeClass('hidden').addClass('selected');

     var $optArrow = $('li[id=' + opt_data_id + '-selectable-li]').find('a.switch i:last');
     $optArrow.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');

     // 全部取消后隐藏
     $('li[id=' + data_id + '-selection-li]').addClass('hidden').removeClass('selected');
     var $selectionLi = $('li[id$=-' + opt_data_id + '-selection-li].selected');
     if ($selectionLi.length == 0){
        $('li[id=' + opt_data_id + '-selection-li]').addClass('hidden').removeClass('selected');
     }
 }

 $('input[name$=' + data_id + '-selection-input]').val(0);
 var $selectableInputs = $('input[id$=' + data_id + '-selectable-input]');
 for (var i=0; i<$selectableInputs.length; i++){
    var $selectableInput = $($selectableInputs[i]);
    $selectableInput.val($selectableInput.attr('max'));
 }
});

// 按件数拆分商品数量
$('.ms-selectable a.btn-minus').click(function(){
 var data_id = $(this).attr('data-id');

 var opt_data_id = data_id.substring(data_id.indexOf('-') + 1);
 $('li[id=' + opt_data_id + '-selection-li]').removeClass('hidden').addClass('selected');
 $('li[id=' + data_id + '-selection-li]').removeClass('hidden').addClass('selected');

 var $optArrow = $('li[id=' + opt_data_id + '-selection-li]').find('a.switch i:last');
 $optArrow.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
　
 // 单SKU选中后隐藏
 var $selectableInput = $('input[id=' + data_id + '-selectable-input]');
 console.log('input:', parseInt($selectableInput.val()||'0'));
 if (parseInt($selectableInput.val()||'0') > 0){
    var calc_val = parseInt($selectableInput.val()||'0') - 1;
    $selectableInput.val(calc_val);
    if (calc_val == 0){
        $('li[id=' + data_id + '-selectable-li]').addClass('hidden').removeClass('selected');
    }
    var $selectionInput = $('input[name=' + data_id + '-selection-input]');
    console.log('minus:',$selectableInput.attr('max') , calc_val);
    $selectionInput.val(parseInt($selectableInput.attr('max')) - calc_val);
 }

 var $selectableLi = $('li[id$=-' + opt_data_id + '-selectable-li].selected');
 if ($selectableLi.length == 0){
    $('li[id=' + opt_data_id + '-selectable-li]').addClass('hidden').removeClass('selected');
 }

});

// 按件数减少拆分数量
$('.ms-selectable a.btn-plus').click(function(){
 var data_id = $(this).attr('data-id');
 var opt_data_id = data_id.substring(data_id.indexOf('-') + 1);
 // 单SKU选中后隐藏
 var $selectableInput = $('input[id=' + data_id + '-selectable-input]');
 var maxInputVal = parseInt($selectableInput.attr('max')||'0');
 if (parseInt($selectableInput.val()||'0') < maxInputVal){
    var calc_val = parseInt($selectableInput.val()||'0') + 1;
    $selectableInput.val(calc_val);
    if (calc_val == maxInputVal){
         $('li[id=' + data_id + '-selection-li]').removeClass('selected').addClass('hidden');
    }
    var $selectionInput = $('input[name=' + data_id + '-selection-input]');
    $selectionInput.val(parseInt(maxInputVal) - calc_val);
 }

 var $selectionLis = $('li[id$=-' + opt_data_id + '-selection-li].selected');
 console.log('select:', $selectionLis);
 if ($selectionLis.length == 0){
    $('li[id=' + opt_data_id + '-selection-li]').addClass('hidden').removeClass('selected');
 }

});

// 可选区列表收起与展开
$('.ms-container a.switch').click(function(){
 var data_id = $(this).attr('data-id');
 var data_channel = $(this).attr('data-channel');
 console.log(data_id, data_channel);
 var selectableLi = $('li[id$=-' + data_id + '-' + data_channel + '-li].selected');
 var optArrow = $(this).find('i:last');
 if (optArrow.hasClass('glyphicon-menu-down')){
     optArrow.removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
     selectableLi.removeClass('hidden');
 }else{
     optArrow.removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
     selectableLi.addClass('hidden');
 }
});

function initModal(){
    var selectedNumObj = {};
    var totalNum = 0;
    var selectedNum = 0;
    var selectedInputs = $('input[name$=-selection-input]');
    for (var i=0; i<selectedInputs.length; i++){
        var $selectInput = $(selectedInputs[i]);
        var oNum = parseInt($selectInput.attr('data-num')||'0');
        var sNum = parseInt($selectInput.val()||'0');
        if (sNum > 0){
            selectedNumObj[$selectInput.attr('name')] = sNum;
        }
        totalNum += oNum;
        selectedNum += sNum;
    }
    console.log('select:', selectedNum, totalNum);
    if (selectedNum > 0) {
            var tempObj = {
            totalNum:totalNum,
            selectedNum:selectedNum,
            supplier:supplier,
            numData:JSON.stringify(selectedNumObj)
        };
        $('#newform .modal-body').html(
            template('forecast-new-tpl', tempObj)
        );
         $('#datepicker').datepicker({
            format: 'yyyy-mm-dd 00:00:00'
        });
        $('#myModal').modal('show');
    }
}

// 初始化
$(function(){

    $("form").submit(function(e){
        e.preventDefault();
        console.log('submit:', $(this));
        var params = {};
        var formDatas = $(this).serializeArray();
        $.each(formDatas,function(index, option){
            console.log('data:', option, index);
            params[option.name] = option.value;
        })
        console.log('params',params);
        $.ajax({
            url:$(this).attr('action'),
            type:'post',
            data: params,
            success: function(resp){
                window.location.href = resp.redirect_url;
            },
            error:function(err){
                var resp = JSON.parse(err.responseText);
                alert(resp.detail);
            },
            dataType:'json'
        });
    });
});