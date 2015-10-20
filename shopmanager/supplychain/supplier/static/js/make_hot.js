/**
 * Created by jishu_linjie on 10/20/15.
 */

function toMakeHot(dom) {
    var id = $(dom).attr('cid');
    console.log('the hot id is :', id);
    console.log('the hot dom is :', dom);

    var url = "/supplychain/supplier/hotpro/";
    var data = {"sale_id": id};
    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
    function callback(res) {
        console.log(res);
        if (res.code == 1) {
            console.log("修改该爆款信息成功");
        }
        else if (res.code == 2) {
            console.log("创建爆款成功");
            // 修改该dom 显示：　查看爆款
            $(dom).html('查看爆款');
            // 添加href 链接到dom
            $(dom).attr("href", "/admin/supplier/hotproduct/?proid=" + id);
        }
        else {
            alert("爆款异常");
        }
    }
}