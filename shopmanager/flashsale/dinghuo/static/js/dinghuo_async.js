//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

function expand(el){
    $(el).closest('div.row').find('table').toggle();
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

function onCheckAll(el){
    $(el).closest('table').find('.check-item').prop('checked', $(el).prop('checked'));
}

function onCheckItemChange(el){
    if(!$(el).closest('table').find('.check-item:checked').length)
        $(el).closest('table').find('.check-all').prop('checked', false);
}

function get_data() {
    var task_id = $("#task_id").val();
    $.ajax({
        url: "/djcelery/" + task_id + "/status/",
        method: "GET",
        success: function (res) {
            console.log("1", res.task.status);
            if (res.task.status == "SUCCESS") {
                $("#loading").hide();
                var result_data = res.task.result.supplier_dict;
                var total_more_num = res.task.result.total_more_num;
                var total_less_num = res.task.result.total_less_num;
                $("#total_more_num").html(total_more_num);
                $("#total_less_num").html(total_less_num);
                $.each(result_data, function (index, supplier) {
                    var products = supplier[1];
                    var supplier_id = products[0][1][0].supplier_id;
                    var supplier_name = products[0][1][0].supplier_name;
                    var supplier_contact = products[0][1][0].supplier_contact;
                    var username = products[0][1][0].username;
                    if(!supplier_id)
                        supplier_name = '未知供应商';
                    var table_dom = $(create_table_dom({
                        supplier_id: supplier_id,
                        supplier_name: supplier_name,
                        supplier_contact: supplier_contact,
                        username: username
                    }));
                    var tb = table_dom.find('tbody');
                    $.each(products, function(index, product){
                        var result_dom;
                        var sku_info = product[1];
                        var sku_length = sku_info.length;
                        var data = {
                            "sku_len": sku_length,
                            "outer_id": product[0],
                            "name": product[1][0].product_name,
                            "pic_path": product[1][0].pic_path
                        };
                        var first_dom = create_first_normal_dom(data);
                        result_dom = first_dom;

                        $.each(sku_info, function (sku_index, sku) {
                            var sku_data = {
                                "sku_name": sku.sku_name,
                                "ding_huo_status": sku.ding_huo_status,
                                "sale_num": sku.sale_num,
                                "product_id": sku.product_id,
                                "sku_id": sku.sku_id,
                                "ding_huo_num": sku.ding_huo_num,
                                "arrival_num": sku.arrival_num,
                                "sample_num": sku.sample_num,
                                "ku_cun_num": sku.ku_cun_num
                            };
                            if(sku.flag_of_more){
                                var second_dom = create_second_blue_dom(sku_data);
                            }else{
                                var second_dom = create_second_red_dom(sku_data);
                            }

                            var last_dom = create_last_dom();
                            result_dom = result_dom + second_dom + last_dom;
                        });
                        if (sku_length == 0){
                            result_dom = result_dom + "<td colspan='7'></tr>";
                        }
                        tb.append(result_dom);
                    });
                    $('#resultPanel').append(table_dom);
                });
            } else {
                setTimeout(get_data, 2000);
            }
        }
    });
}

function create_table_dom(obj){
    function table_dom(){
        /*
         <div class="row">
         <h2>
             {{ supplier_name }}
             <span style="font-size:70%">
                 {{ supplier_contact }}
             </span>
             <span style="font-size:70%">
                 {{ username }}
             </span>
             <a href="javascript:;" onclick="expand(this);" style="font-size: 50%; color:#01b5a2">展开</a>
         </h2>
         <table class="table table-bordered" style="display:none">
         <thead style="background-color:#01B5A2;">
         <th width="250px">
         商品信息<br>
         <div class="checkbox" style="margin-top:0"><label><input type="checkbox" class="check-all" onclick="onCheckAll(this);">全选</label></div>
         </th>
         <th width="100px">图片</th>
         <th>尺寸</th>
         <th width="150px">状态</th>
         <th>销售数</th>
         <th>已拍(未到)数量</th>
         <th>已到数量</th>
         <th>样品数量</th>
         <th>上架前库存数</th>
         </thead>
         <tbody></tbody>
         </table>
         </div>
         */
    }
    return hereDoc(table_dom).template(obj);
}


function create_first_normal_dom(obj) {
    function first_normal_dom() {
        /*
         <tr data-outer-id="{{ outer_id }}">
         <td rowspan="{{ sku_len }}">{{ name }}<br>
         <a href="/sale/dinghuo/adddetail/{{ outer_id }}" target="_blank">编码:{{ outer_id }}</a><br>
         <a href="/sale/dinghuo/change_kucun/?search_input={{ outer_id }}" target="_blank">修改上架前库存</a><br>
         <div class="checkbox" style="margin-top:0"><label><input type="checkbox" class="check-item" onchange="onCheckItemChange(this);">选择</label></div>
         </td>
         <td rowspan="{{ sku_len }}">
         <div class="portfolio-box"><div class="portfolio-box"><img src="{{ pic_path }}?imageView2/0/w/100" width="100px"
         class="img-circle"></div></td>
         */
    };
    return hereDoc(first_normal_dom).template(obj);
}

function create_second_red_dom(obj) {
    function second_red_dom() {
        /*
         <td>{{ sku_name }}</td>
         <td><span style="color: red;font-size: 20px">{{ ding_huo_status }}</span></td>
         <td>{{ sale_num }}</td>
         <td><a href="/sale/dinghuo/statsbypid/{{ product_id }}" target="_blank"
         id="ding_huo_num_{{ sku_id }}">{{ ding_huo_num }}</a></td>
         <td>{{ arrival_num }}</td>
         <td>{{ sample_num }}</td>
         <td>{{ ku_cun_num }}</td>
         */

    };

    return hereDoc(second_red_dom).template(obj);
}

function create_second_blue_dom(obj) {
    function second_blue_dom() {
        /*
         <td>{{ sku_name }}</td>
         <td><span style="color: blue;font-size: 20px">{{ ding_huo_status }}</span></td>
         <td>{{ sale_num }}</td>
         <td><a href="/sale/dinghuo/statsbypid/{{ product_id }}" target="_blank"
         id="ding_huo_num_{{ sku_id }}">{{ ding_huo_num }}</a></td>
         <td>{{ arrival_num }}</td>
         <td>{{ sample_num }}</td>
         <td>{{ ku_cun_num }}</td>
         */

    };

    return hereDoc(second_blue_dom).template(obj);
}

function create_last_dom() {
    function last_dom() {
        /*
         </tr>
         */
    };

    return hereDoc(last_dom).template();
}
