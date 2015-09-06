/**
 * Created by timi06 on 15-7-30.
 */
function show_seckill_list_shop(obj) {
    function carts_dom() {
/*
	<li>
      <a href="pages/shangpinxq.html?id={{ id }}">
        <img src="{{ pic_path }}">
        <p class="gname">{{ name }}</p>
        <p class="gprice">
          <span class="nprice"><em>¥</em> {{ agent_price }} </span>
          <s class="oprice"><em>¥</em> {{ std_sale_price }}</s>
        </p>{{ saleout_dom }}
      </a>
    </li>	 */
    };
    return hereDoc(carts_dom).template(obj)
}
//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}


function Set_orders() {
    //请求URL
    var requestUrl = "/rest/v1/products/seckill";

    //请求成功回调函数
    var requestCallBack = function (data) {
        $("#loading").hide();
        if (data.results != "undefined" && data.results.length != 0) {

            // 头图
            $('#tips').html('<a href="pages/shangpinxq.html?id='+data.results[0].id+'"><img src="'+data.results[0].pic_path+'"></a>')
            $.each(data.results,
                function (index, product) {
                    if (index == 0){
                        return
                    }
                    var cart_dom = show_seckill_list_shop(product);
                    $('#prod_list').append(cart_dom);
                }
            );
        }
    };
    // 发送请求
    $.ajax({
        type: 'get',
        url: requestUrl,
        data: {},
        dataType: 'json',
        beforeSend: function () {
            $("#loading").show();
        },
        success: requestCallBack
    });
}

function need_set_info(){
	//获取设置帐号的信息
	var requestUrl = GLConfig.baseApiUrl + "/users/need_set_info";

	var requestCallBack = function(res){
        var result = res.result;
        if(result=="yes" || result == "1"){
            $(".p-center").append('<span class="center-red-dot"></span>');
        }

	};
	// 请求推荐数据
	$.ajax({
		type:'get',
		url:requestUrl,
		data:{},
		dataType:'json',
		success:requestCallBack
	});
}