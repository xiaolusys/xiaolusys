function buyer_select(el){
    var buyer_id = $(el).val() - 0;
    var orderlist_id = $(el).attr('orderlist-id') - 0;
    $.ajax({
        url: '/sale/dinghuo/dinghuo_orderlist/' + orderlist_id + '/change_buyer',
        type: 'post',
        dataType: 'json',
        data: {buyer_id: buyer_id}
    });
}
