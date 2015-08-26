$(function () {
    $(".color-choose").click(dynamic_generat);
    $(".sku-choose").click(dynamic_generat);
})
function dynamic_generat() {
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

}