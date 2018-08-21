//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}
//字符串模板
String.prototype.template = function (data) {
    var str = this;
    if (data && data.sort) {
        for (var i = 0; i < data.length; i++) {
            str = str.replace(new RegExp("{\\{" + i + "}}", "gm"), data[i]);
        }
        return str;
    }

    var placeholder = str.match(new RegExp("{{.+?}}", 'ig'));
    if (data && placeholder) {
        for (var i = 0; i < placeholder.length; i++) {
            var key = placeholder[i];
            var value = proxy.call(data, key.replace(new RegExp("[{,}]", "gm"), ""));
            key = key.replace(new RegExp("\\\.", "gm"), "\\.").replace("{{", "{\\{");
            if (value == null)
                value = "&nbsp;";
            str = str.replace(new RegExp(key, "gm"), value);
        }
    }
    return str;

    function proxy(key) {
        try {
            return eval('this.' + key);
        } catch (e) {
            return "";
        }
    }
};

get_data();
function get_data() {
    $("#loading").show();
    var task_id = $("#task_id").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/", //这里是静态页的地址
        method: "GET", //静态页用get方法，否则服务器会抛出405错误
        success: function (res) {
            console.log("1", res.task.status);
            if (res.task.status == "SUCCESS") {
                $("#loading").hide();
                var result_data = res.task.result;
                $("#total_num").html(result_data.total_num);
                $("#total_cost").html(result_data.total_cost);
                $("#total_sales").html(result_data.total_sales);
                $("#post_fees").html(result_data.post_fees);
                $("#trade_nums").html(result_data.trade_nums);
                $("#refund_fees").html(result_data.refund_fees);
                $("#buyer_nums").html(result_data.buyer_nums);
                if (result_data.empty_order_count > 0) {
                    $("#empty_order_count_link").show();
                    $("#empty_order_count").html("有 " + result_data.empty_order_count + " 个订单的商品编码异常>>");
                }

                var item_list = result_data.trade_items;

                var tb = $('#result-data-field');
                $.each(item_list, function (index, dd) {
                    var result_dom;
                    var product_info = dd[1];
                    var sku_info = product_info.skus;


                    var data = {
                        "sku_len": sku_info.length,
                        "outer_id": dd[0],
                        "sale_charger": product_info.sale_charger,
                        "product_id": product_info.product_id,
                        "pic_path": product_info.pic_path,
                        "title": product_info.title,
                        "num": product_info.num,
                        "cost": product_info.cost.toFixed(2),
                        "sales": product_info.sales.toFixed(2)
                    }

                    if (sku_info.length > 0) {
                        var first_warning = product_info.cost >= product_info.sales || sku_info[0][1].cost >= sku_info[0][1].sales;
                        var first_dom = create_first_normal_dom(data);
                        if (first_warning) {
                            first_dom = create_first_waring_dom(data);
                        }
                        result_dom = first_dom;

                        $.each(sku_info, function (sku_index, sku) {
                            var sku_data = {
                                "sku_id": sku[0],
                                "sku_name": sku[1].sku_name,
                                "num": sku[1].num,
                                "cost": sku[1].cost.toFixed(2),
                                "sales": sku[1].sales.toFixed(2)
                            }
                            if (sku_index == 0) {
                                var second_dom = create_second_normal_dom(sku_data);
                                var last_dom = create_last_dom();
                                result_dom = result_dom + second_dom + last_dom;
                                tb.append(result_dom);
                            } else {

                                var inner_waring = sku[1].cost >= sku[1].sales;
                                var tr_dom = create_tr_dom();
                                if (inner_waring) {
                                    tr_dom = create_tr_waring_dom();
                                }
                                var second_dom = create_second_normal_dom(sku_data);
                                var last_dom = create_last_dom();
                                result_dom = tr_dom + second_dom + last_dom;
                                tb.append(result_dom);
                            }
                        });
                    } else {
                        var waring_dom = create_waring_dom(data);
                        tb.append(waring_dom);
                    }
                });
            } else {
                setTimeout(get_data, 1000);
            }
        }
    });
}


function create_first_normal_dom(obj) {
    function first_normal_dom() {
        /*
         <tr>
         <td rowspan="{{ sku_len }}">{{ outer_id }}
         <p>买:[{{ sale_charger }}]</p>

         <p>仓:[{{ storage_charger }}]</p></td>
         <td rowspan="{{ sku_len }}">
         <a href="/admin/items/product/{{ product_id }}/"
         target="_blank">
         <img src="{{ pic_path }}" title="{{ title }}"
         width="180px" height="80px"/>
         </a>
         <label>{{ title }}</label>
         </td>
         <td rowspan="{{ sku_len }}">{{ num }}</td>
         <td rowspan="{{ sku_len }}">{{ cost }}</td>
         <td rowspan="{{ sku_len }}">{{ sales }}</td>
         */
    };

    return hereDoc(first_normal_dom).template(obj)
}

function create_first_waring_dom(obj) {
    function first_waring_dom() {
        /*
         <tr class="label-warning">
         <td rowspan="{{ sku_len }}">{{ outer_id }}
         <p>买:[{{ sale_charger }}]</p>

         <p>仓:[{{ storage_charger }}]</p></td>
         <td rowspan="{{ sku_len }}">
         <a href="/admin/items/product/{{ product_id }}/"
         target="_blank">
         <img src="{{ pic_path }}" title="{{ title }}"
         width="180px" height="80px"/>
         </a>
         <label>{{ title }}</label>
         </td>
         <td rowspan="{{ sku_len }}">{{ num }}</td>
         <td rowspan="{{ sku_len }}">{{ cost }}</td>
         <td rowspan="{{ sku_len }}">{{ sales }}</td>
         */
    };

    return hereDoc(first_waring_dom).template(obj)
}
function create_second_normal_dom(obj) {
    function second_normal_dom() {
        /*
         <td>{{ sku_id }}</td>
         <td>{{ sku_name }}</td>
         <td>{{ num }}</td>
         <td>{{ cost }}</td>
         <td>{{ sales }}</td>
         */
    };

    return hereDoc(second_normal_dom).template(obj)
}

function create_tr_dom() {
    function tr_dom() {
        /*
         <tr>
         */
    };

    return hereDoc(tr_dom).template()
}
function create_tr_waring_dom() {
    function tr_dom() {
        /*
         <tr class="label-warning">
         */
    };

    return hereDoc(tr_dom).template()
}
function create_last_dom() {
    function last_dom() {
        /*
         </tr>
         */
    };

    return hereDoc(last_dom).template()
}


function create_waring_dom(obj) {
    function dom() {
        /*
         <tr class="label-danger">
         <td >{{ outer_id }}</td>
         <td >{{ title }}</td>
         <td >{{ num }}</td>
         <td >{{ cost }}</td>
         <td >{{ sales }}</td>
         <td colspan="5">--</td>
         </tr>
         */
    };

    return hereDoc(dom).template(obj)
}