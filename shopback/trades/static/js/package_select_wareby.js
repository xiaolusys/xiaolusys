function ware_by_select(el){
    var wareby_id = $(el).val() - 0;
    var wareby_id = $(el).attr('wareby-id') - 0;
    var package_id = $(el).data('package-id');
    $.ajax({
        url: '/trades/package_order/new_create',
        type: 'post',
        dataType: 'json',
        data: {"ware_by_id": wareby_id, "package_id": package_id},
        success:function(){
            alert("修改仓库成功");
        }
    });
}
