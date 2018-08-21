$(".category_select").live("change", function (e) {
    e.preventDefault();

    var target = e.target;
    var pid = target.getAttribute('pid');
    var cat_id = $(target).val();

    var url = "/items/product/" + pid + "/?format=json";
    var callback = function (res) {
        if (res.code == 0 && res.response_content.category.cid.toString() == cat_id) {
            $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
        }
    };

    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {
        "csrfmiddlewaretoken": csrf_token,
        "format": "json",
        "category": cat_id
    };

    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
});

$(".ware_select").live("change", function (e) {
    e.preventDefault();

    var target = e.target;
    var pid = target.getAttribute('pid');
    var cat_id = $(target).val();

    var url = "/items/product/" + pid + "/?format=json";
    var callback = function (res) {
        if (res.code == 0 && res.response_content.ware_by.toString() == cat_id) {
            $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
        }
    };

    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {
        "csrfmiddlewaretoken": csrf_token,
        "format": "json",
        "ware_by": cat_id
    };

    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
});

$(".charger_select").live("change", function (e) {
    e.preventDefault();

    var target = e.target;
    var pid = target.getAttribute('cid');
    var charger = $(target).val();

    var url = "/items/product/" + pid + "/?format=json";
    var callback = function (res) {
        if (res.code == 0 && res.response_content.storage_charger != '') {
            $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
        }
    };

    var csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    var data = {
        "csrfmiddlewaretoken": csrf_token,
        "format": "json",
        "storage_charger": charger
    };

    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
});


$(".purchase_charger_select").live("change", function (e) {
    e.preventDefault();

    var target = e.target;
    var uid = target.getAttribute('cid');
    var groupid = $(target).val();
    var url = "/sale/dinghuo/setusertogroup/";
    var callback = function (res) {
        console.log(res);
        if (res == "OK") {
            $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
        }
    };
    var data = {"groupid": groupid, "uid": uid};
    $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
});

$(function () {

    $(".select_saletime").datepicker({
        dateFormat: "yy-mm-dd"
    }).change(function (e) {
        var item_id = this.id;
        var sale_time = this.value;
        var sale_time_old = this.name;
        var target = e.target;
        var url = "/items/select_sale_time/";
        var callback = function (res) {

            if (res == "OK") {
                $(target).after("<img src='/static/admin/img/icon-yes.gif '>");
            }
        };
        var data = {"item_id": item_id, "sale_time": sale_time};
        if (confirm("确定要修改日期吗？")) {
            $.ajax({"url": url, "data": data, "success": callback, "type": "POST"});
        } else {
            this.value = sale_time_old;
        }


    });
});