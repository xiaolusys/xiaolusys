/**
 * Created by linjie on 15-7-10.
 */


function select_buyter(id) {
    var element_id = "item_id_" + id;
    var group_element = "select_buyer_group_" + id;
    var group = document.getElementById(group_element).value;
    var name = document.getElementById(element_id).innerText;
    var url = "/supplychain/supplier/buyer_group/";
    var data = {"name": name, "group": group};

    function callback(res) {
        if (res == 'changeok') {
            console.log(res);
        }
        else if (res == 'createok') {
            console.log(res);
        }
        else {
            console.log('something error is hanppend!');
        }
    }

    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
}

//  product/(?P<pk>[0-9]+)/
function sale_librarian_select(dom) {
    // 修改资料员
    var librarian = $(dom).val();
    var spid = $(dom).attr('spid');
    var url = "/supplychain/supplier/product_change/" + spid + '/';
    var data = {"librarian": librarian};

    console.log(librarian, spid);
    $.ajax({"url": url, "data": data, "success": callback, "type": "post"});
    function callback(res) {
        console.log(res);
    }
}


function sale_buyer_select(dom) {
    // 修改采购员
    var buyer = $(dom).val();
    var spid = $(dom).attr('spid');
    var url = "/supplychain/supplier/product_change/" + spid + '/';
    var data = {"buyer": buyer};

    console.log(buyer, spid);
    $.ajax({"url": url, "data": data, "success": callback, "type": "post"});
    function callback(res) {
        console.log(res);
    }
}
