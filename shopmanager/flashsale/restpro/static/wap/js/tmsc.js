/**
 * Created by yann on 15-7-24.
 */
function create_shop_carts_dom(obj){
	function carts_dom(){
    /*
    <div class="item">
        <div class="gpic"><img src="{{ pic_path}}"></div>
        <div class="gname">{{ title }}</div>
        <div class="gprice">¥ {{ total_fee}}</div>
        <div class="gsize">尺码：{{sku_name}}</div>
        <div class="goprice"><s>¥168</s></div>
        <div class="btn-del"></div>
        <div class="gcount">
            <div class="btn reduce"></div>
            <div class="total">
                <input type="tel" value="{{num}}">
            </div>
            <div class="btn plus"></div>
        </div>
    </div>
    */};
  return hereDoc(carts_dom).template(obj)
}
//定义多行字符串函数实现
function hereDoc(f) {
    return f.toString().replace(/^[^\/]+\/\*!?\s?/, '').replace(/\*\/[^\/]+$/, '');
}

function get_shop_carts(suffix){
	//请求URL
	var requestUrl = GLConfig.baseApiUrl + suffix;

	//请求成功回调函数
	var requestCallBack = function(data){
        var total_price = 0;
		if (data.count != 'undefined' && data.count != null){
			$.each(data.results,
				function(index,product){
                    total_price += product.total_fee;
					var cart_dom = create_shop_carts_dom(product);
					$('.cart-list').append(cart_dom);
				}
			);
		}
        $("#total_price").html(total_price);
	};
	// 发送请求
	$.ajax({
		type:'get',
		url:requestUrl,
		data:{},
		dataType:'json',
		success:requestCallBack
	});
}