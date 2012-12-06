goog.provide('ordercheck');

goog.provide('ordercheck.Dialog');

goog.require('goog.dom');
goog.require('goog.ui.Dialog');
goog.require('goog.style');

/** @constructor */
ordercheck.Dialog = function (manager) {
    this.dialog = new goog.ui.Dialog();
    this.init();
    this.commentManager = manager;

}


ordercheck.Dialog.prototype.init = function () {
    this.dialog.setContent(
	'<div class="container" style="width:720px">'
	    +'<div class="row-fluid">'
	    +'<div class="span3"><label style="color:#999;display:inline">订单号: </label>240108925675896</div>'
	    +'<div class="span3"><label style="color:#999;display:inline">买家: </label>季中仁2008</div>'
	    +'<div class="span3"><label style="color:#999;display:inline">店铺: </label>优尼小小世界</div>'
	    +'<div class="span3"><label style="color:#999;display:inline">付款时间: </label>2012-11-29 13:27</div>'
	    +'</div>'
	    +'<div class="row-fluid">'
	    +'<div class="alert alert-warning"><strong>买家留言: </strong>90 cm 缺货 不要了等有货了再买 10/30 lynn 90 cm 缺货 不要了等有货了再买 10/30 lynn</div>'
	    +'<div class="alert alert-error"><strong>卖家留言: </strong>客人又反悔了  直接发货</div>'
	    +'</div>'
	    +'<div style="padding:9px 15px">'
	    +'<label style="color:#999;display:inline">快递: </label>'
	    +'<select id="select01">'
	    +'<option>中通速递</option>'
	    +'<option>圆通速递</option>'
	    +'<option>申通速递</option>'
	    +'<option>顺丰速递</option>'
	    +'</select>'
	    +'</div>'
	    +'<div class="accordion-group">  '
	    +'<div class="accordion-heading"> '
	    +'<div style="padding:2px 15px">'
	    +'<div class="row-fluid">'
	    +'<div class="span7"><label style="color:#999;display:inline">地址: </label>浙江省, 温州市, 永嘉县, 浙江省永嘉县瓯北镇罗浮大街282号</div>'
	    +'<div class="span5"><label style="color:#999;display:inline">手机: </label>13616611892 <label style="color:#999;display:inline">固话: </label>021-58863259</div>'
	    +'</div>'
	    +'</div>'
            +'<a class="accordion-toggle" style="padding:0px 15px" data-toggle="collapse" href="#collapseOne">修改地址››</a>  '
	    +'</div>'
	    +'<div id="collapseOne" class="accordion-body collapse" style="height: 0px; ">  '
            +'<div class="accordion-inner">  '
	    +'<form class="form-inline">'
	    +'<div>'
	    +'<label style="color:#999;display:inline">新地址: </label>'
	    +'<input type="text" class="input-small" placeholder="省">'
	    +'<input type="text" class="input-small" placeholder="市">'
	    +'<input type="text" class="input-small" placeholder="区">'
	    +'<input type="text" style="width:310px" placeholder="详细地址">'
	    +'</div>'
	    +'<div style="margin-top:5px;margin-left:46px;width:630px">'
	    +'<input type="text" class="input-small" placeholder="手机">'
	    +'<input type="text" class="input-small" placeholder="固话">'
	    +'<input type="submit" class="btn btn-small" style="float:right" value="确定修改">'
	    +'</div>'
	    +'</form>'
            +'</div>'
	    +'</div>'
	    +'</div>'
	    +'<div style="padding:9px 15px">'
	    +'<ul class="thumbnails">'
	    +'<li><span class="badge badge-warning">有留言</span></li><li><span class="badge badge-important">待退款</span></li><li><span class="badge badge-inverse">缺货</span></li><li><span class="badge badge-info">信息不全</span></li><li><span class="badge badge-info">订单合并</span>'
	    +'</ul>'
	    +'</div>'
	    +'<div class="accordion-group">'
	    +'<div class="accordion-heading" style="margin: 5px 0px">'
            +'<a class="accordion-toggle" style="padding:0px 15px" data-toggle="collapse" href="#collapseTwo">商品列表››</a>'
	    +'</div>'
	    +'<div id="collapseTwo" class="accordion-body collapse" style="height: 0px; ">'
            +'<div class="accordion-inner">'
	    +'<form class="well form-search">'
	    +'<input type="text" class="input-medium search-query">'
	    +'<select id="select02">'
	    +'<option>商家编码</option>'
	    +'<option>商品简称</option>'
	    +'</select>'
	    +'<button type="submit" class="btn">商品搜索</button>'
	    +'<div style="height:10px"></div>'
	    +'<table class="table table-bordered table-striped table-condensed fixed-layout">'
	    +'<thead>'
	    +'<tr>'
	    +'<td>编号</td><td>商家编码</td><td>商品简称</td><td>规格</td><td>数量</td><td>正品单价</td><td>操作</td>'
	    +'</tr>'
	    +'</thead>'
	    +'<tbody>'
	    +'<tr>'
	    +'<td>1</td>'
	    +'<td>ABCDEFG</td>'
	    +'<td>竹纤维凉毯盖毯</td>'
	    +'<td><div>120*60</div><div>枫叶</div></td>'
	    +'<td>1</td>'
	    +'<td>99.00</td>'
	    +'<td><a type="submit" class="btn btn-small">添加</a></td>'
	    +'</tr>'
	    +'<tr>'
	    +'<td>2</td>'
	    +'<td>ABCDEFG</td>'
	    +'<td>竹纤维凉毯盖毯</td>'
	    +'<td><div>120*60</div><div>枫叶</div></td>'
	    +'<td>1</td>'
	    +'<td>99.00</td>'
	    +'<td><a href="#" class="btn btn-small">添加</a></td>'
	    +'</tr>'
	    +'</tbody>'
	    +'</table>'
	    +'</form>'
	    +'<table class="table table-bordered table-striped table-condensed fixed-layout">'
	    +'<thead>'
	    +'<tr>'
	    +'<td>编号</td><td>商家编码</td><td>商品简称</td><td>规格</td><td>数量</td><td>正品单价</td><td>操作</td>'
	    +'</tr>'
	    +'</thead>'
	    +'<tbody>'
	    +'<tr>'
	    +'<td>1</td>'
	    +'<td>ABCDEFG</td>'
	    +'<td>竹纤维凉毯盖毯</td>'
	    +'<td><div>120*60</div><div>枫叶</div></td>'
	    +'<td>1</td>'
	    +'<td>99.00</td>'
	    +'<td><a class="btn btn-small" href="#"><i class="icon-remove"></i> 删除</a></td>'
	    +'</tr>'
	    +'<tr>'
	    +'<td>2</td>'
	    +'<td>ABCDEFG</td>'
	    +'<td>竹纤维凉毯盖毯</td>'
	    +'<td><div>120*60</div><div>枫叶</div></td>'
	    +'<td>1</td>'
	    +'<td>99.00</td>'
	    +'<td><a class="btn btn-small" href="#"><i class="icon-remove"></i> 删除</a></td>'
	    +'</tr>'
	    +'</tbody>'
	    +'</table>'
            +'</div>'
	    +'</div>'
	    +'</div>');
    this.dialog.setTitle('订单审核详情');
    this.dialog.setButtonSet(new goog.ui.Dialog.ButtonSet().addButton({key: 'OK', caption: "审核通过"},true,false));

    //</li><li style="float:right"><button type="submit" class="btn btn-success">审核通过</button></li>
    goog.events.listen(this.dialog, goog.ui.Dialog.EventType.SELECT, this);
}

ordercheck.Dialog.prototype.show = function(data) {
    this.dialog.setVisible(true);
    //if (data != null) {
    //    var scoreDom = goog.dom.getElement("id-select-score");
    //    scoreDom.value = data.score;
    //    var textDom = goog.dom.getElement("id-input-textarea");
    //    textDom.value = data.text;
    //}
}

ordercheck.Dialog.prototype.handleEvent= function (e) {
    if (e.key == 'OK') {
        //var scoreDom = goog.dom.getElement("id-select-score");
        //var textDom = goog.dom.getElement("id-input-textarea");
        ////var retval = this.commentManager.addComment(scoreDom.value, textDom.value);
        //if (retval == false) {
        //    return false;
        //}
        //textDom.value = "";
        //scoreDom.value = "0";
    }
    return true;
}

goog.provide("ordercheck.Manager");
ordercheck.Manager = function () {
    this.dialog = new ordercheck.Dialog(this);
    this.button = goog.dom.getElement("id-button");
    goog.events.listen(this.button, goog.events.EventType.CLICK, this.showDialog, false, this);
}

ordercheck.Manager.prototype.showDialog = function() {
    this.dialog.show();
}

new ordercheck.Manager();