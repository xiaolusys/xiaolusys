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
        if (data.count != 'undifine' && data.count != null) {
            console.log('debug results:', data.results);
            $("#loading").hide();
            $.each(data.results,
                function (index, product) {

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