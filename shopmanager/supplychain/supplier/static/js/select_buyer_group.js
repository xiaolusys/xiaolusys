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
        else if (res=='createok') {
            console.log(res);
        }
        else {
            console.log('something error is hanppend!');
        }
    }

    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
}